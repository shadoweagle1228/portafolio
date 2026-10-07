"""Adaptador de entrada: API REST (FastAPI)."""
from __future__ import annotations

import re
from dataclasses import asdict

from typing import Any

from fastapi import FastAPI, HTTPException, Path

from auditor.adapters.s3_inspector import Boto3BucketInspector
from auditor.application.ports import BucketInspector
from auditor.application.use_cases import AuditAllBuckets, AuditBucket

BUCKET_RE = re.compile(r"^[a-z0-9][a-z0-9.-]{2,62}$")


def create_app(inspector: BucketInspector | None = None) -> FastAPI:
    actual_inspector = inspector or Boto3BucketInspector()
    app = FastAPI(title="Bucket PCI Auditor", docs_url=None, redoc_url=None)
    audit_one, audit_all = AuditBucket(actual_inspector), AuditAllBuckets(actual_inspector)

    @app.get("/healthz")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/audit")
    def audit_everything() -> list[dict[str, Any]]:
        return [asdict(r) | {"compliant": r.compliant} for r in audit_all()]

    @app.get("/audit/{bucket}")
    def audit_bucket(bucket: str = Path(..., max_length=63)) -> dict[str, Any]:
        if not BUCKET_RE.match(bucket):  # validacion de entrada (security first)
            raise HTTPException(status_code=422, detail="Nombre de bucket invalido")
        report = audit_one(bucket)
        return asdict(report) | {"compliant": report.compliant}

    return app
