"""Stack efimero: asistente RAG en AWS. Pensado para `cdk deploy` y `cdk destroy` a voluntad.

Costo: solo pago por uso (Lambda, Bedrock, S3); sin recursos con costo fijo (sin OpenSearch ni NAT).
Todo se elimina con `cdk destroy` (bucket vaciado automaticamente, log groups y guardrail incluidos).
"""
from pathlib import Path

from aws_cdk import CfnOutput, Duration, RemovalPolicy, Stack, Tags
from aws_cdk import aws_bedrock as bedrock
from aws_cdk import aws_budgets as budgets
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_logs as logs
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_s3_deployment as s3deploy
from constructs import Construct

SRC = Path(__file__).resolve().parents[1] / "src"
SAMPLE_DOCS = Path(__file__).resolve().parents[1] / "sample-docs"
_PROFILE_PREFIXES = ("us.", "eu.", "apac.")


def _model_arns(stack: Stack, model_id: str) -> list[str]:
    """ARNs minimos para invocar un modelo (foundation model y, si aplica, su inference profile)."""
    if model_id.startswith(_PROFILE_PREFIXES):
        base = model_id.split(".", 1)[1]
        return [
            f"arn:{stack.partition}:bedrock:*::foundation-model/{base}",
            f"arn:{stack.partition}:bedrock:{stack.region}:{stack.account}:inference-profile/{model_id}",
        ]
    return [f"arn:{stack.partition}:bedrock:{stack.region}::foundation-model/{model_id}"]


class RagAssistantStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        generation_model_id: str,
        embedding_model_id: str,
        budget_email: str | None = None,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # --- Almacenamiento (efimero: se borra con destroy) ---
        bucket = s3.Bucket(
            self, "Knowledge",
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            object_ownership=s3.ObjectOwnership.BUCKET_OWNER_ENFORCED,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )
        s3deploy.BucketDeployment(
            self, "SampleDocs",
            sources=[s3deploy.Source.asset(str(SAMPLE_DOCS))],
            destination_bucket=bucket,
            destination_key_prefix="docs",
        )

        # --- Guardrail: PII/tarjetas, contenido danino y prompt injection ---
        filters = [
            bedrock.CfnGuardrail.ContentFilterConfigProperty(type=t, input_strength="HIGH", output_strength="HIGH")
            for t in ("SEXUAL", "VIOLENCE", "HATE", "INSULTS", "MISCONDUCT")
        ] + [
            bedrock.CfnGuardrail.ContentFilterConfigProperty(
                type="PROMPT_ATTACK", input_strength="HIGH", output_strength="NONE"
            )
        ]
        guardrail = bedrock.CfnGuardrail(
            self, "Guardrail",
            name="rag-assistant-guardrail",
            blocked_input_messaging="Tu consulta fue bloqueada por las politicas de seguridad.",
            blocked_outputs_messaging="La respuesta fue bloqueada por las politicas de seguridad.",
            content_policy_config=bedrock.CfnGuardrail.ContentPolicyConfigProperty(filters_config=filters),
            sensitive_information_policy_config=bedrock.CfnGuardrail.SensitiveInformationPolicyConfigProperty(
                pii_entities_config=[
                    bedrock.CfnGuardrail.PiiEntityConfigProperty(type=t, action="BLOCK")
                    for t in ("CREDIT_DEBIT_CARD_NUMBER", "CREDIT_DEBIT_CARD_CVV", "AWS_SECRET_KEY", "PASSWORD")
                ]
            ),
        )

        # --- Lambdas ---
        env = {
            "DOCS_BUCKET": bucket.bucket_name,
            "EMBED_MODEL_ID": embedding_model_id,
            "GEN_MODEL_ID": generation_model_id,
            "GUARDRAIL_ID": guardrail.attr_guardrail_id,
            "GUARDRAIL_VERSION": "DRAFT",
            "MIN_SCORE": "0.3",
        }

        def make_function(name: str, handler: str, timeout: int) -> lambda_.Function:
            log_group = logs.LogGroup(
                self, f"{name}Logs", retention=logs.RetentionDays.ONE_WEEK, removal_policy=RemovalPolicy.DESTROY
            )
            return lambda_.Function(
                self, name,
                runtime=lambda_.Runtime.PYTHON_3_12,
                handler=handler,
                code=lambda_.Code.from_asset(str(SRC)),
                timeout=Duration.seconds(timeout),
                memory_size=512,
                environment=env,
                log_group=log_group,
            )

        ingest_fn = make_function("Ingest", "handlers.ingest.handler", 300)
        query_fn = make_function("Query", "handlers.query.handler", 90)  # > 2 llamadas con timeout propio

        # --- Permisos minimos ---
        bucket.grant_read(ingest_fn)
        bucket.grant_put(ingest_fn, "index/*")
        bucket.grant_read(query_fn, "index/*")
        ingest_fn.add_to_role_policy(iam.PolicyStatement(
            actions=["bedrock:InvokeModel"], resources=_model_arns(self, embedding_model_id)))
        query_fn.add_to_role_policy(iam.PolicyStatement(
            actions=["bedrock:InvokeModel"],
            resources=_model_arns(self, embedding_model_id) + _model_arns(self, generation_model_id)))
        query_fn.add_to_role_policy(iam.PolicyStatement(
            actions=["bedrock:ApplyGuardrail"], resources=[guardrail.attr_guardrail_arn]))

        # --- Control de gasto (cuenta personal) ---
        if budget_email:
            budgets.CfnBudget(
                self, "Budget",
                budget=budgets.CfnBudget.BudgetDataProperty(
                    budget_type="COST", time_unit="MONTHLY",
                    budget_limit=budgets.CfnBudget.SpendProperty(amount=5, unit="USD"),
                ),
                notifications_with_subscribers=[budgets.CfnBudget.NotificationWithSubscribersProperty(
                    notification=budgets.CfnBudget.NotificationProperty(
                        notification_type="ACTUAL", comparison_operator="GREATER_THAN",
                        threshold=80, threshold_type="PERCENTAGE"),
                    subscribers=[budgets.CfnBudget.SubscriberProperty(
                        subscription_type="EMAIL", address=budget_email)],
                )],
            )

        Tags.of(self).add("Project", "portafolio")
        Tags.of(self).add("Purpose", "ephemeral-demo")

        CfnOutput(self, "KnowledgeBucketName", value=bucket.bucket_name)
        CfnOutput(self, "IngestFunctionName", value=ingest_fn.function_name)
        CfnOutput(self, "QueryFunctionName", value=query_fn.function_name)
