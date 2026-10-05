"""Construct reutilizable: bucket S3 alineado a PCI DSS v4.0."""
from aws_cdk import Duration, RemovalPolicy, Tags
from aws_cdk import aws_iam as iam
from aws_cdk import aws_kms as kms
from aws_cdk import aws_s3 as s3
from constructs import Construct

PCI_LOG_RETENTION_DAYS = 365  # Req. 10.5.1


class SecureBucket(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        bucket_name: str,
        environment: str,
        owner: str,
        data_classification: str = "cardholder-data",
        log_retention_days: int = PCI_LOG_RETENTION_DAYS,
    ) -> None:
        super().__init__(scope, construct_id)
        if log_retention_days < PCI_LOG_RETENTION_DAYS:
            raise ValueError("PCI DSS 10.5.1 exige >= 365 dias de retencion de logs")

        is_prod = environment == "prod"
        removal = RemovalPolicy.RETAIN if is_prod else RemovalPolicy.DESTROY

        self.key = kms.Key(
            self, "Key",
            alias=f"alias/{bucket_name}",
            enable_key_rotation=True,          # Req. 3.7.4
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
                        s3.Transition(
                            storage_class=s3.StorageClass.GLACIER,
                            transition_after=Duration.days(90),
                        )
                    ]
                )
            ],
            removal_policy=RemovalPolicy.RETAIN,
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

        self.bucket.add_to_resource_policy(
            iam.PolicyStatement(
                sid="DenyUnencryptedUploads",
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
