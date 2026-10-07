"""Handler de consulta: composition root + garantia de respuesta + metrica EMF."""
from __future__ import annotations

import json
import os
import time

from rag.adapters.bedrock import BedrockEmbedder, BedrockGenerator
from rag.adapters.s3_store import S3VectorStore
from rag.application import ERROR_ANSWER, AnswerQuestion
from rag.domain import Chunk

_CACHE_TTL_SECONDS = 300
_use_case: AnswerQuestion | None = None


class _CachedStore:
    """Evita leer el indice de S3 en cada invocacion; se refresca cada 5 minutos."""

    def __init__(self, inner: S3VectorStore) -> None:
        self._inner, self._chunks, self._loaded_at = inner, [], 0.0

    def load(self) -> list[Chunk]:
        if time.time() - self._loaded_at > _CACHE_TTL_SECONDS:
            self._chunks, self._loaded_at = self._inner.load(), time.time()
        return self._chunks

    def save(self, chunks: list[Chunk]) -> None:  # pragma: no cover - solo lectura aqui
        raise NotImplementedError


def _build() -> AnswerQuestion:
    return AnswerQuestion(
        embedder=BedrockEmbedder(model_id=os.environ["EMBED_MODEL_ID"]),
        store=_CachedStore(S3VectorStore(os.environ["DOCS_BUCKET"])),
        generator=BedrockGenerator(
            model_id=os.environ["GEN_MODEL_ID"],
            guardrail_id=os.environ.get("GUARDRAIL_ID"),
            guardrail_version=os.environ.get("GUARDRAIL_VERSION", "DRAFT"),
        ),
        min_score=float(os.environ.get("MIN_SCORE", "0.3")),
    )


def _emit_metric(status: str) -> None:
    print(json.dumps({
        "_aws": {
            "Timestamp": int(time.time() * 1000),
            "CloudWatchMetrics": [{
                "Namespace": "RagAssistant",
                "Dimensions": [["Status"]],
                "Metrics": [{"Name": "Responses", "Unit": "Count"}],
            }],
        },
        "Status": status,
        "Responses": 1,
    }))


def handler(event, context):
    global _use_case
    request_id = getattr(context, "aws_request_id", "local")
    try:
        _use_case = _use_case or _build()
        answer = _use_case((event or {}).get("question", ""))
        status, text, sources = answer.status, answer.text, list(answer.sources)
    except Exception:  # noqa: BLE001 - error de configuracion/arranque: igual se responde
        status, text, sources = "error", ERROR_ANSWER, []
    _emit_metric(status)
    return {"status": status, "answer": text, "sources": sources, "request_id": request_id}
