"""Casos de uso."""
from __future__ import annotations

from auditor.application.ports import BucketInspector
from auditor.domain.model import AuditReport, evaluate


class AuditBucket:
    def __init__(self, inspector: BucketInspector) -> None:
        self._inspector = inspector

    def __call__(self, bucket_name: str) -> AuditReport:
        return evaluate(self._inspector.inspect(bucket_name))


class AuditAllBuckets:
    def __init__(self, inspector: BucketInspector) -> None:
        self._inspector = inspector
        self._audit = AuditBucket(inspector)

    def __call__(self) -> list[AuditReport]:
        return [self._audit(name) for name in self._inspector.list_buckets()]
