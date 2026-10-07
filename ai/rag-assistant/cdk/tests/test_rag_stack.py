import aws_cdk as cdk
import pytest
from aws_cdk.assertions import Match, Template

from rag_stack import RagAssistantStack

ENV = cdk.Environment(account="111122223333", region="us-east-1")


def synth(**kwargs) -> Template:
    app = cdk.App()
    stack = RagAssistantStack(
        app, "T", generation_model_id="amazon.nova-lite-v1:0",
        embedding_model_id="amazon.titan-embed-text-v2:0", env=ENV, **kwargs,
    )
    return Template.from_stack(stack)


@pytest.fixture(scope="module")
def template() -> Template:
    return synth()


def test_everything_is_destroyable(template):
    buckets = template.find_resources("AWS::S3::Bucket")
    assert buckets and all(b["DeletionPolicy"] == "Delete" for b in buckets.values())
    for group in template.find_resources("AWS::Logs::LogGroup").values():
        assert group["DeletionPolicy"] == "Delete"
    template.has_resource_properties("AWS::S3::Bucket", {
        "Tags": Match.array_with([{"Key": "aws-cdk:auto-delete-objects", "Value": "true"}])
    })


def test_bucket_is_private_encrypted_and_tls_only(template):
    template.has_resource_properties("AWS::S3::Bucket", {
        "PublicAccessBlockConfiguration": {
            "BlockPublicAcls": True, "BlockPublicPolicy": True,
            "IgnorePublicAcls": True, "RestrictPublicBuckets": True},
        "BucketEncryption": Match.any_value(),
    })
    template.has_resource_properties("AWS::S3::BucketPolicy", {
        "PolicyDocument": {"Statement": Match.array_with([
            Match.object_like({"Effect": "Deny", "Condition": {"Bool": {"aws:SecureTransport": "false"}}})])}
    })


def test_both_lambdas_exist_with_expected_handlers(template):
    for handler in ("handlers.ingest.handler", "handlers.query.handler"):
        template.has_resource_properties("AWS::Lambda::Function", {"Handler": handler, "Runtime": "python3.12"})


def test_query_timeout_covers_two_bedrock_calls(template):
    template.has_resource_properties("AWS::Lambda::Function", {"Handler": "handlers.query.handler", "Timeout": 90})


def test_guardrail_blocks_cards_and_prompt_attacks(template):
    template.has_resource_properties("AWS::Bedrock::Guardrail", {
        "SensitiveInformationPolicyConfig": {"PiiEntitiesConfig": Match.array_with(
            [{"Type": "CREDIT_DEBIT_CARD_NUMBER", "Action": "BLOCK"}])},
        "ContentPolicyConfig": {"FiltersConfig": Match.array_with(
            [Match.object_like({"Type": "PROMPT_ATTACK", "InputStrength": "HIGH"})])},
    })


def test_bedrock_permissions_are_least_privilege(template):
    bedrock_statements = []
    for policy in template.find_resources("AWS::IAM::Policy").values():
        for st in policy["Properties"]["PolicyDocument"]["Statement"]:
            actions = st["Action"] if isinstance(st["Action"], list) else [st["Action"]]
            if any(a.startswith("bedrock:") for a in actions):
                bedrock_statements.append((actions, st["Resource"]))
    assert bedrock_statements
    for actions, resource in bedrock_statements:
        assert "bedrock:*" not in actions and resource != "*"


def test_budget_only_when_email_is_given(template):
    assert not template.find_resources("AWS::Budgets::Budget")
    with_budget = synth(budget_email="tu@correo.com")
    with_budget.resource_count_is("AWS::Budgets::Budget", 1)
