"""Construct reutilizable: bucket S3 alineado a PCI DSS v4.0."""
from aws_cdk import CfnOutput, Duration, RemovalPolicy, Stack, Tags
from aws_cdk import aws_iam as iam
from aws_cdk import aws_kms as kms
from aws_cdk import aws_s3 as s3
from constructs import Construct

PCI_LOG_RETENTION_DAYS = 365  # Req. 10.5.1

KEY_ADMIN_ACTIONS = [
    "kms:Create*", "kms:Describe*", "kms:Enable*", "kms:List*", "kms:Put*", "kms:Update*",
    "kms:Revoke*", "kms:Disable*", "kms:Get*", "kms:Delete*", "kms:TagResource",
    "kms:UntagResource", "kms:ScheduleKeyDeletion", "kms:CancelKeyDeletion",
]
KEY_USER_ACTIONS = [
    "kms:Encrypt", "kms:Decrypt", "kms:ReEncrypt*", "kms:GenerateDataKey*", "kms:DescribeKey",
]


class SecureBucket(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        bucket_name: str,
        environment: str,
        owner: str,
        key_admin_role_arns: list[str],
        key_user_role_arns: list[str],
        data_classification: str = "cardholder-data",
        log_retention_days: int = PCI_LOG_RETENTION_DAYS,
    ) -> None:
        super().__init__(scope, construct_id)
        if log_retention_days < PCI_LOG_RETENTION_DAYS:
            raise ValueError("PCI DSS 10.5.1 exige >= 365 dias de retencion de logs")
        if not key_admin_role_arns or not key_user_role_arns:
            raise ValueError("Se requieren administradores y usuarios de la llave KMS")

        stack = Stack.of(self)
        # Logs con politica de bucket (no ACL): necesario con BucketOwnerEnforced.
        # Debe fijarse antes de crear los buckets hijos.
        self.node.set_context("@aws-cdk/aws-s3:serverAccessLogsUseBucketPolicy", True)
        is_prod = environment == "prod"
        removal = RemovalPolicy.RETAIN if is_prod else RemovalPolicy.DESTROY

        # Req. 7: politica explicita (sin statement de root kms:*) con separacion de funciones.
        # Los administradores conservan kms:PutKeyPolicy para evitar el bloqueo de la llave.
        key_policy = iam.PolicyDocument(
            statements=[
                iam.PolicyStatement(
                    sid="KeyAdministrators",
                    effect=iam.Effect.ALLOW,
                    principals=[iam.ArnPrincipal(a) for a in key_admin_role_arns],
                    actions=KEY_ADMIN_ACTIONS,
                    resources=["*"],
                ),
                iam.PolicyStatement(
                    sid="KeyUsersViaS3Only",
                    effect=iam.Effect.ALLOW,
                    principals=[iam.ArnPrincipal(a) for a in key_user_role_arns],
                    actions=KEY_USER_ACTIONS,
                    resources=["*"],
                    conditions={
                        "StringEquals": {
                            "kms:ViaService": f"s3.{stack.region}.amazonaws.com",
                            "kms:CallerAccount": stack.account,
                        }
                    },
                ),
            ]
        )
        self.key = kms.Key(
            self, "Key",
            alias=f"alias/{bucket_name}",
            enable_key_rotation=True,          # Req. 3.7.4
            policy=key_policy,
            removal_policy=RemovalPolicy.RETAIN,
        )

        self.logs_bucket = s3.Bucket(
            self, "Logs",
            bucket_name=f"{bucket_name}-logs",
            object_lock_enabled=True,           # Req. 10.3
            object_lock_default_retention=s3.ObjectLockRetention.compliance(
                Duration.days(log_retention_days)
            ),
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            versioned=True,
            object_ownership=s3.ObjectOwnership.BUCKET_OWNER_ENFORCED,
            lifecycle_rules=[
                s3.LifecycleRule(
                    transitions=[
                        # Acceso inmediato durante los 12 meses (Req. 10.5.1)
                        s3.Transition(
                            storage_class=s3.StorageClass.GLACIER_INSTANT_RETRIEVAL,
                            transition_after=Duration.days(90),
                        )
                    ]
                )
            ],
            removal_policy=RemovalPolicy.RETAIN,
        )

        # Confused deputy: solo el bucket de datos puede entregar logs aqui.
        # El ARN se arma con el nombre (no con la referencia) para evitar dependencia circular.
        self.logs_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                sid="AllowS3ServerAccessLogsFromDataBucketOnly",
                effect=iam.Effect.ALLOW,
                principals=[iam.ServicePrincipal("logging.s3.amazonaws.com")],
                actions=["s3:PutObject"],
                resources=[self.logs_bucket.arn_for_objects("*")],
                conditions={
                    "ArnEquals": {"aws:SourceArn": f"arn:{stack.partition}:s3:::{bucket_name}"},
                    "StringEquals": {"aws:SourceAccount": stack.account},
                },
            )
        )

        self.bucket = s3.Bucket(
            self, "Data",
            bucket_name=bucket_name,
            encryption=s3.BucketEncryption.KMS,
            encryption_key=self.key,
            bucket_key_enabled=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,   # Req. 1 / 7
            enforce_ssl=True,                                      # Req. 4.2.1
            minimum_tls_version=1.2,
            versioned=True,
            object_ownership=s3.ObjectOwnership.BUCKET_OWNER_ENFORCED,
            server_access_logs_bucket=self.logs_bucket,
            server_access_logs_prefix=f"{bucket_name}/",
            lifecycle_rules=[
                s3.LifecycleRule(
                    noncurrent_version_expiration=Duration.days(365),
                    abort_incomplete_multipart_upload_after=Duration.days(7),
                )
            ],
            removal_policy=removal,
            auto_delete_objects=not is_prod,
        )

        # "IfExists": subidas SIN header se cifran con el KMS por defecto;
        # solo se bloquean las que piden explicitamente otro algoritmo (p. ej. AES256).
        self.bucket.add_to_resource_policy(
            iam.PolicyStatement(
                sid="DenyExplicitNonKmsEncryption",
                effect=iam.Effect.DENY,
                principals=[iam.AnyPrincipal()],
                actions=["s3:PutObject"],
                resources=[self.bucket.arn_for_objects("*")],
                conditions={
                    "StringNotEqualsIfExists": {"s3:x-amz-server-side-encryption": "aws:kms"}
                },
            )
        )

        for construct in (self.bucket, self.logs_bucket, self.key):
            Tags.of(construct).add("Environment", environment)
            Tags.of(construct).add("DataClassification", data_classification)
            Tags.of(construct).add("Owner", owner)
            Tags.of(construct).add("Compliance", "pci-dss-v4")
            # Req. 10.2: debe estar cubierto por CloudTrail data events
            Tags.of(construct).add("AuditTrail", "cloudtrail-s3-data-events-required")

        CfnOutput(
            self, "CloudTrailDataEventsResourceArn",
            description="Agregar a los Advanced Event Selectors del trail (S3 data events, Req. 10.2)",
            value=f"{self.bucket.bucket_arn}/",
        )
