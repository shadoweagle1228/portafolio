import aws_cdk as cdk
import pytest
from aws_cdk.assertions import Match, Template

from secure_s3.storage_stack import StorageStack


@pytest.fixture(scope="module")
def template() -> Template:
    app = cdk.App()
    return Template.from_stack(StorageStack(app, "T", environment="dev"))


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


def test_tls_enforced(template):
    template.has_resource_properties("AWS::S3::BucketPolicy", {
        "PolicyDocument": {"Statement": Match.array_with([
            Match.object_like({"Effect": "Deny", "Condition": {"Bool": {"aws:SecureTransport": "false"}}})
        ])}
    })
