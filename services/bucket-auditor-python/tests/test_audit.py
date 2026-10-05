"""Test del dominio y casos de uso con un fake (sin AWS)."""
from auditor.application.use_cases import AuditBucket
from auditor.domain.model import BucketConfiguration


class FakeInspector:
    def __init__(self, cfg): self.cfg = cfg
    def inspect(self, name): return self.cfg
    def list_buckets(self): return [self.cfg.name]


def compliant_cfg(**over):
    base = dict(name="b", public_access_blocked=True, encryption_algorithm="aws:kms",
                kms_rotation_enabled=True, versioning_enabled=True,
                access_logging_enabled=True, tls_enforced=True)
    return BucketConfiguration(**(base | over))


def test_compliant_bucket_has_no_findings():
    assert AuditBucket(FakeInspector(compliant_cfg()))("b").compliant


def test_public_bucket_is_critical():
    report = AuditBucket(FakeInspector(compliant_cfg(public_access_blocked=False)))("b")
    assert [f.rule_id for f in report.findings] == ["S3-001"]
    assert report.findings[0].severity.value == "CRITICAL"


def test_multiple_findings():
    report = AuditBucket(FakeInspector(compliant_cfg(tls_enforced=False, access_logging_enabled=False)))("b")
    assert {f.rule_id for f in report.findings} == {"S3-004", "S3-005"}
