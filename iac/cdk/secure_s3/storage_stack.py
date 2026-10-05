from aws_cdk import CfnOutput, Stack
from constructs import Construct

from secure_s3.secure_bucket import SecureBucket


class StorageStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, *, environment: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        secure = SecureBucket(
            self, "CdeData",
            bucket_name=f"edwin-portafolio-{environment}-cde-data",
            environment=environment,
            owner="platform-team",
        )
        CfnOutput(self, "BucketArn", value=secure.bucket.bucket_arn)
        CfnOutput(self, "KmsKeyArn", value=secure.key.key_arn)
