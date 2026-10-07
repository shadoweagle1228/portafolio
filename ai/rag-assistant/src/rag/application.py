"""Casos de uso. Garantia clave: AnswerQuestion SIEMPRE devuelve una respuesta."""
from __future__ import annotations

import logging
from dataclasses import dataclass

from rag.domain import SYSTEM_PROMPT, Chunk, build_user_prompt, chunk_text, retrieve
from rag.ports import DocumentSource, Embedder, Generator, VectorStore

logger = logging.getLogger(__name__)

MAX_QUESTION_CHARS = 2000
NO_CONTEXT_ANSWER = "No tengo informacion suficiente en la base de conocimiento para responder eso."
ERROR_ANSWER = "No pude procesar tu consulta en este momento. Intenta de nuevo en unos minutos."
INVALID_ANSWER = "Envia una pregunta no vacia de maximo 2000 caracteres."


@dataclass(frozen=True)
class Answer:
    status: str  # answered | no_context | invalid | error
    text: str
    sources: tuple[str, ...] = ()


class IngestDocuments:
    def __init__(self, source: DocumentSource, embedder: Embedder, store: VectorStore) -> None:
        self._source, self._embedder, self._store = source, embedder, store

    def __call__(self) -> int:
        chunks: list[Chunk] = []
        for name, text in self._source.list_documents():
            for c in chunk_text(name, text):
                chunks.append(Chunk(c.source, c.text, tuple(self._embedder.embed(c.text))))
        self._store.save(chunks)
        return len(chunks)


class AnswerQuestion:
    def __init__(self, embedder: Embedder, store: VectorStore, generator: Generator,
                 top_k: int = 4, min_score: float = 0.3) -> None:
        self._embedder, self._store, self._generator = embedder, store, generator
        self._top_k, self._min_score = top_k, min_score

    def __call__(self, question: str) -> Answer:
        question = (question or "").strip()
        if not question or len(question) > MAX_QUESTION_CHARS:
            return Answer("invalid", INVALID_ANSWER)
        try:
            found = retrieve(self._embedder.embed(question), self._store.load(), self._top_k, self._min_score)
            if not found:
                return Answer("no_context", NO_CONTEXT_ANSWER)
            text = self._generator.generate(SYSTEM_PROMPT, build_user_prompt(question, found))
            sources = tuple(dict.fromkeys(r.chunk.source for r in found))
            return Answer("answered", text, sources)
        except Exception:  # noqa: BLE001 - por diseno: nunca dejar al usuario sin respuesta
            logger.exception("Fallo al responder")
            return Answer("error", ERROR_ANSWER)
