"""Adaptadores de salida: documentos e indice vectorial en S3 (sin servicios vectoriales con costo fijo)."""
from __future__ import annotations

import json

import boto3
from botocore.exceptions import ClientError

from rag.domain import Chunk

DOCS_PREFIX = "docs/"
INDEX_KEY = "index/vectors.json"
_TEXT_SUFFIXES = (".md", ".txt")


class S3DocumentSource:
    def __init__(self, bucket: str, s3_client=None) -> None:
        self._bucket, self._s3 = bucket, s3_client or boto3.client("s3")

    def list_documents(self) -> list[tuple[str, str]]:
        documents: list[tuple[str, str]] = []
        for page in self._s3.get_paginator("list_objects_v2").paginate(Bucket=self._bucket, Prefix=DOCS_PREFIX):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                if key.lower().endswith(_TEXT_SUFFIXES):
                    body = self._s3.get_object(Bucket=self._bucket, Key=key)["Body"].read().decode("utf-8")
                    documents.append((key.removeprefix(DOCS_PREFIX), body))
        return documents


class S3VectorStore:
    def __init__(self, bucket: str, s3_client=None) -> None:
        self._bucket, self._s3 = bucket, s3_client or boto3.client("s3")

    def save(self, chunks: list[Chunk]) -> None:
        payload = [{"source": c.source, "text": c.text, "embedding": list(c.embedding)} for c in chunks]
        self._s3.put_object(
            Bucket=self._bucket, Key=INDEX_KEY, Body=json.dumps(payload).encode("utf-8"),
            ContentType="application/json",
        )

    def load(self) -> list[Chunk]:
        try:
            body = self._s3.get_object(Bucket=self._bucket, Key=INDEX_KEY)["Body"].read()
        except ClientError as error:
            if error.response["Error"]["Code"] == "NoSuchKey":
                return []
            raise
        return [Chunk(i["source"], i["text"], tuple(i["embedding"])) for i in json.loads(body)]
