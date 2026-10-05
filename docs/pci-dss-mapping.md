# Mapeo PCI DSS v4.0 → controles implementados

| Requisito v4.0 | Control | CloudFormation | Terraform | CDK |
|----------------|---------|:-:|:-:|:-:|
| 1.4 / 7.2 — Sin acceso público, mínimo privilegio | Public Access Block, `BucketOwnerEnforced` (sin ACLs) | ✅ | ✅ | ✅ |
| 3.5.1 — Datos almacenados ilegibles | SSE-KMS con CMK + Bucket Key; deny de uploads sin KMS | ✅ | ✅ | ✅ |
| 3.7.4 — Rotación de llaves | `EnableKeyRotation` | ✅ | ✅ | ✅ |
| 4.2.1 — Criptografía fuerte en tránsito | `aws:SecureTransport` + `s3:TlsVersion >= 1.2` | ✅ | ✅ | ✅ |
| 10.2.1 — Logs de auditoría | S3 server access logs | ✅ | ✅ | ✅ |
| 10.3.2 / 10.3.4 — Integridad/protección de logs | Bucket de logs con Object Lock COMPLIANCE + versionado | ✅ | ✅ | ✅ |
| 10.5.1 — Retención 12 meses (3 inmediatos) | 365 días de retención; Glacier a los 90 días | ✅ | ✅ | ✅ |
| 6.3.2 / 6.3.3 — Inventario y vulnerabilidades | pip-audit, OWASP dependency-check, Trivy en CI | — | — | — |
| 6.2.x — Desarrollo seguro | Hexagonal, validación de entrada, SAST (Bandit, Sonar) | — | — | — |
| 8.x — Autenticación | OIDC en pipelines (sin llaves estáticas), Keycloak como IdP | — | — | — |
| 1.x — Segmentación de red | EKS con API privada, NetworkPolicy default-deny | — | — | — |

## Brechas conocidas (a cubrir en el roadmap)
- CloudTrail data events + GuardDuty S3 Protection (Req. 10 / 11).
- Replicación cross-region y backup (Req. 12.10 / resiliencia).
- Política de acceso por rol (principals) específica de cada aplicación (Req. 7.2.x).
- cdk-nag aún no incluye un pack PCI DSS 4.0; se usa PCI DSS 3.2.1 como aproximación.
