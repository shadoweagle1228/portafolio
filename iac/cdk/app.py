#!/usr/bin/env python3
import aws_cdk as cdk
from aws_cdk import Aspects
import cdk_nag

from secure_s3.storage_stack import StorageStack

app = cdk.App()
env_name = app.node.try_get_context("environment") or "dev"
stack = StorageStack(app, f"SecureStorage-{env_name}", environment=env_name)

# cdk-nag: reglas AWS Solutions + PCI DSS 3.2.1 (la mas cercana disponible a v4)
Aspects.of(app).add(cdk_nag.AwsSolutionsChecks(verbose=True))
Aspects.of(app).add(cdk_nag.PCIDSS321Checks(verbose=True))

app.synth()
