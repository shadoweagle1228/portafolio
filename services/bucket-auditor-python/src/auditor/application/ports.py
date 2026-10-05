"""Puertos (interfaces) que el dominio/aplicacion necesita."""
from __future__ import annotations

from typing import Protocol

from auditor.domain.model import BucketConfiguration


class BucketInspector(Protocol):
    """Puerto de salida: obtener la configuracion real de un bucket."""

    def inspect(self, bucket_name: str) -> BucketConfiguration: ...

    def list_buckets(self) -> list[str]: ...
