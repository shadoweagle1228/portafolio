import aws_cdk as cdk
import pytest
from aws_cdk.assertions import Match, Template

from secure_s3.storage_stack import StorageStack

ADMIN = "arn:aws:iam::111122223333:role/key-admin"
USER = "arn:aws:iam::111122223333:role/app-role"


@pytest.fixture(scope="module")
def template() -> Template:
    app = cdk.App()
    stack = StorageStack(
        app, "T", environment="dev",
        key_admin_role_arns=[ADMIN], key_user_role_arns=[USER],
        env=cdk.Environment(account="111122223333", region="us-east-1"),
    )
    return Template.from_stack(stack)


def test_all_buckets_block_public_access(template):
    buckets = template.find_resources("AWS::S3::Bucket")
    assert len(buckets) == 2
    for b in buckets.values():
        assert b["Properties"]["PublicAccessBlockConfiguration"] == {
            "BlockPublicAcls": True, "BlockPublicPolicy": True,
            "IgnorePublicAcls": True, "RestrictPublicBuckets": True,
        }


def test_kms_rotation_enabled(template):
    template.has_resource_properties("AWS::KMS::Key", {"EnableKeyRotation": True})


def test_kms_policy_separates_duties_and_has_no_root_wildcard(template):
    (key,) = template.find_resources("AWS::KMS::Key").values()
    statements = key["Properties"]["KeyPolicy"]["Statement"]
    assert {s["Sid"] for s in statements} == {"KeyAdministrators", "KeyUsersViaS3Only"}
    admin = next(s for s in statements if s["Sid"] == "KeyAdministrators")
    user = next(s for s in statements if s["Sid"] == "KeyUsersViaS3Only")
    assert "kms:Decrypt" not in admin["Action"] and "kms:Encrypt" not in admin["Action"]
    assert "kms:*" not in str(statements)
    assert user["Condition"]["StringEquals"]["kms:ViaService"] == "s3.us-east-1.amazonaws.com"


def test_data_bucket_encrypted_with_kms(template):
    template.has_resource_properties("AWS::S3::Bucket", {
        "BucketEncryption": {"ServerSideEncryptionConfiguration": [Match.object_like(
            {"ServerSideEncryptionByDefault": Match.object_like({"SSEAlgorithm": "aws:kms"})}
        )]}
    })


def test_logs_bucket_is_immutable(template):
    template.has_resource_properties("AWS::S3::Bucket", {
        "ObjectLockConfiguration": Match.object_like(
            {"Rule": {"DefaultRetention": {"Mode": "COMPLIANCE", "Days": 365}}}
        )
    })


def test_logs_transition_to_instant_retrieval(template):
    template.has_resource_properties("AWS::S3::Bucket", {
        "LifecycleConfiguration": {"Rules": [Match.object_like(
            {"Transitions": [Match.object_like({"StorageClass": "GLACIER_IR"})]}
        )]}
    })


def test_logs_policy_restricts_source_arn(template):
    template.has_resource_properties("AWS::S3::BucketPolicy", {
        "PolicyDocument": {"Statement": Match.array_with([Match.object_like({
            "Sid": "AllowS3ServerAccessLogsFromDataBucketOnly",
            "Condition": {"ArnEquals": {"aws:SourceArn": Match.object_like({
                "Fn::Join": Match.array_with([Match.array_with([":s3:::edwin-portafolio-dev-cde-data"])])
            })},
            "StringEquals": {"aws:SourceAccount": "111122223333"}},
        })])}
    })


def test_tls_enforced(template):
    template.has_resource_properties("AWS::S3::BucketPolicy", {
        "PolicyDocument": {"Statement": Match.array_with([
            Match.object_like({"Effect": "Deny", "Condition": {"Bool": {"aws:SecureTransport": "false"}}})
        ])}
    })


def test_cloudtrail_data_events_output_and_tag(template):
    outputs = template.to_json()["Outputs"]
    assert any("CloudTrailDataEventsResourceArn" in k for k in outputs)
    template.has_resource_properties("AWS::KMS::Key", {
        "Tags": Match.array_with([{"Key": "AuditTrail", "Value": "cloudtrail-s3-data-events-required"}])
    })
