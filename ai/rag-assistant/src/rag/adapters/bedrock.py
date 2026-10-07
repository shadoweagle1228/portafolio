"""Adaptador de salida: Amazon Bedrock (embeddings y generacion)."""
from __future__ import annotations

import json

import boto3
from botocore.config import Config

_CONFIG = Config(read_timeout=20, connect_timeout=5, retries={"max_attempts": 2, "mode": "standard"})


def _client():
    return boto3.client("bedrock-runtime", config=_CONFIG)


class BedrockEmbedder:
    def __init__(self, client=None, model_id: str = "amazon.titan-embed-text-v2:0", dimensions: int = 512) -> None:
        self._client = client or _client()
        self._model_id, self._dimensions = model_id, dimensions

    def embed(self, text: str) -> list[float]:
        body = json.dumps({"inputText": text, "dimensions": self._dimensions, "normalize": True})
        response = self._client.invoke_model(
            modelId=self._model_id, body=body, contentType="application/json", accept="application/json"
        )
        return json.loads(response["body"].read())["embedding"]


class BedrockGenerator:
    def __init__(self, client=None, model_id: str = "amazon.nova-lite-v1:0",
                 guardrail_id: str | None = None, guardrail_version: str = "DRAFT") -> None:
        self._client = client or _client()
        self._model_id = model_id
        self._guardrail = (
            {"guardrailIdentifier": guardrail_id, "guardrailVersion": guardrail_version} if guardrail_id else None
        )

    def generate(self, system: str, user: str) -> str:
        kwargs = {
            "modelId": self._model_id,
            "system": [{"text": system}],
            "messages": [{"role": "user", "content": [{"text": user}]}],
            "inferenceConfig": {"maxTokens": 600, "temperature": 0.0},
        }
        if self._guardrail:
            kwargs["guardrailConfig"] = self._guardrail
        response = self._client.converse(**kwargs)
        return response["output"]["message"]["content"][0]["text"]
