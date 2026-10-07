"""Pruebas sin AWS: fakes deterministas para embeddings, almacen y generador."""
import zlib

import pytest

from rag.application import (ERROR_ANSWER, INVALID_ANSWER, NO_CONTEXT_ANSWER, AnswerQuestion, IngestDocuments)
from rag.domain import SYSTEM_PROMPT, Chunk, chunk_text, cosine, retrieve

DIMS = 64


class FakeEmbedder:
    """Bolsa de palabras hasheada: determinista y suficiente para probar la logica."""

    def embed(self, text):
        vec = [0.0] * DIMS
        for token in text.lower().split():
            vec[zlib.crc32(token.encode()) % DIMS] += 1.0
        return vec


class FakeStore:
    def __init__(self, chunks=None): self.chunks = chunks or []
    def save(self, chunks): self.chunks = list(chunks)
    def load(self): return self.chunks


class FakeSource:
    def list_documents(self):
        return [("s3.md", "bucket cifrado con kms rotacion de llaves"),
                ("k8s.md", "keycloak desplegado en kubernetes con networkpolicy")]


class FakeGenerator:
    def __init__(self): self.calls = []
    def generate(self, system, user):
        self.calls.append((system, user))
        return "respuesta basada en contexto [s3.md]"


class ExplodingEmbedder:
    def embed(self, text): raise RuntimeError("bedrock caido")


def indexed_store():
    store = FakeStore()
    IngestDocuments(FakeSource(), FakeEmbedder(), store)()
    return store


def test_chunking_respects_max_and_overlap():
    chunks = chunk_text("a.md", "x" * 2000, max_chars=800, overlap=100)
    assert all(len(c.text) <= 800 for c in chunks) and len(chunks) >= 3


def test_chunking_rejects_bad_params():
    with pytest.raises(ValueError):
        chunk_text("a.md", "texto", max_chars=100, overlap=100)


def test_cosine_identical_and_zero():
    assert cosine([1, 0], [1, 0]) == pytest.approx(1.0)
    assert cosine([0, 0], [1, 0]) == 0.0


def test_ingest_indexes_every_document():
    store = indexed_store()
    assert {c.source for c in store.chunks} == {"s3.md", "k8s.md"}
    assert all(c.embedding for c in store.chunks)


def test_answers_with_sources_when_context_found():
    generator = FakeGenerator()
    answer = AnswerQuestion(FakeEmbedder(), indexed_store(), generator, min_score=0.2)("cifrado bucket kms")
    assert answer.status == "answered" and answer.sources == ("s3.md",)
    assert "<contexto>" in generator.calls[0][1]


def test_no_context_does_not_call_the_model():
    generator = FakeGenerator()
    answer = AnswerQuestion(FakeEmbedder(), indexed_store(), generator, min_score=0.2)("receta de paella valenciana")
    assert (answer.status, answer.text) == ("no_context", NO_CONTEXT_ANSWER)
    assert generator.calls == []   # anti-alucinacion: sin contexto no se genera


@pytest.mark.parametrize("question", ["", "   ", "x" * 2001])
def test_invalid_questions_get_a_response(question):
    answer = AnswerQuestion(FakeEmbedder(), indexed_store(), FakeGenerator())(question)
    assert (answer.status, answer.text) == ("invalid", INVALID_ANSWER)


def test_backend_failure_still_returns_a_response():
    answer = AnswerQuestion(ExplodingEmbedder(), indexed_store(), FakeGenerator())("cualquier cosa")
    assert (answer.status, answer.text) == ("error", ERROR_ANSWER)   # cero respuestas perdidas


def test_retrieve_orders_by_score_and_applies_threshold():
    chunks = [Chunk("a", "a", (1.0, 0.0)), Chunk("b", "b", (0.7, 0.7)), Chunk("c", "c", (0.0, 1.0))]
    result = retrieve([1.0, 0.0], chunks, top_k=2, min_score=0.5)
    assert [r.chunk.source for r in result] == ["a", "b"]


def test_system_prompt_defends_against_prompt_injection():
    assert "DATOS" in SYSTEM_PROMPT and "ignora" in SYSTEM_PROMPT
