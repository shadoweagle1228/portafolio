"""Handler de ingesta: lee docs/ de S3, genera embeddings y guarda index/vectors.json."""
from __future__ import annotations

import os

from rag.adapters.bedrock import BedrockEmbedder
from rag.adapters.s3_store import S3DocumentSource, S3VectorStore
from rag.application import IngestDocuments


def handler(event, context):
    bucket = os.environ["DOCS_BUCKET"]
    ingest = IngestDocuments(
        source=S3DocumentSource(bucket),
        embedder=BedrockEmbedder(model_id=os.environ["EMBED_MODEL_ID"]),
        store=S3VectorStore(bucket),
    )
    return {"chunks_indexed": ingest()}
