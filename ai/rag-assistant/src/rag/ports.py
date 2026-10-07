"""Puertos que necesita la aplicacion."""
from __future__ import annotations

from typing import Protocol

from rag.domain import Chunk


class Embedder(Protocol):
    def embed(self, text: str) -> list[float]: ...


class VectorStore(Protocol):
    def save(self, chunks: list[Chunk]) -> None: ...

    def load(self) -> list[Chunk]: ...


class DocumentSource(Protocol):
    def list_documents(self) -> list[tuple[str, str]]:
        """Devuelve pares (nombre, texto)."""
        ...


class Generator(Protocol):
    def generate(self, system: str, user: str) -> str: ...
