"""Dominio puro: sin dependencias de frameworks ni de AWS."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"


@dataclass(frozen=True)
class BucketConfiguration:
    """Estado observado de un bucket (value object)."""
    name: str
    public_access_blocked: bool
    encryption_algorithm: str | None
    kms_rotation_enabled: bool | None
    versioning_enabled: bool
    access_logging_enabled: bool
    tls_enforced: bool


@dataclass(frozen=True)
class Finding:
    rule_id: str
    pci_requirement: str
    severity: Severity
    message: str


@dataclass(frozen=True)
class AuditReport:
    bucket: str
    findings: tuple[Finding, ...] = field(default_factory=tuple)

    @property
    def compliant(self) -> bool:
        return not self.findings


def evaluate(config: BucketConfiguration) -> AuditReport:
    """Reglas de negocio PCI DSS v4.0 aplicadas a un bucket."""
    findings: list[Finding] = []

    if not config.public_access_blocked:
        findings.append(Finding("S3-001", "1.4 / 7.2", Severity.CRITICAL,
                                "El acceso publico no esta completamente bloqueado"))
    if config.encryption_algorithm != "aws:kms":
        findings.append(Finding("S3-002", "3.5.1", Severity.HIGH,
                                "El bucket no usa cifrado SSE-KMS con CMK"))
    elif config.kms_rotation_enabled is False:
        findings.append(Finding("S3-003", "3.7.4", Severity.MEDIUM,
                                "La CMK no tiene rotacion automatica"))
    if not config.tls_enforced:
        findings.append(Finding("S3-004", "4.2.1", Severity.HIGH,
                                "La politica no obliga TLS (aws:SecureTransport)"))
    if not config.access_logging_enabled:
        findings.append(Finding("S3-005", "10.2.1", Severity.HIGH,
                                "No hay logging de acceso habilitado"))
    if not config.versioning_enabled:
        findings.append(Finding("S3-006", "10.3.4", Severity.MEDIUM,
                                "El versionado no esta habilitado"))

    return AuditReport(bucket=config.name, findings=tuple(findings))
