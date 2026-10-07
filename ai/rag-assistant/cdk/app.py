#!/usr/bin/env python3
"""Uso:
  cdk deploy  -c budget_email=tu@correo.com
  cdk destroy
Contexto opcional: generation_model_id, embedding_model_id (ver README).
"""
import os

import aws_cdk as cdk

from rag_stack import RagAssistantStack

app = cdk.App()
RagAssistantStack(
    app, "RagAssistant",
    generation_model_id=app.node.try_get_context("generation_model_id") or "amazon.nova-lite-v1:0",
    embedding_model_id=app.node.try_get_context("embedding_model_id") or "amazon.titan-embed-text-v2:0",
    budget_email=app.node.try_get_context("budget_email"),
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"),
        region=os.getenv("CDK_DEFAULT_REGION") or "us-east-1",
    ),
)
app.synth()
