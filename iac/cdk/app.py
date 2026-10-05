#!/usr/bin/env python3
import aws_cdk as cdk
import cdk_nag
from aws_cdk import Aspects

from secure_s3.storage_stack import StorageStack


def _arns(app: cdk.App, key: str) -> list[str]:
    raw = app.node.try_get_context(key) or ""
    return [a.strip() for a in raw.split(",") if a.strip()]


app = cdk.App()
env_name = app.node.try_get_context("environment") or "dev"
# Uso: cdk deploy -c environment=dev -c key_admin_role_arns=arn1,arn2 -c key_user_role_arns=arn3
stack = StorageStack(
    app, f"SecureStorage-{env_name}",
    environment=env_name,
    key_admin_role_arns=_arns(app, "key_admin_role_arns"),
    key_user_role_arns=_arns(app, "key_user_role_arns"),
)

# cdk-nag: reglas AWS Solutions + PCI DSS 3.2.1 (la mas cercana disponible a v4)
Aspects.of(app).add(cdk_nag.AwsSolutionsChecks(verbose=True))
Aspects.of(app).add(cdk_nag.PCIDSS321Checks(verbose=True))

app.synth()
