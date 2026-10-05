# Plantilla de reporte WAFR / SecCheck

> Documento confidencial. Anonimiza cliente, cuentas y recursos antes de publicar.

## 1. Resumen ejecutivo
- **Carga de trabajo:** `<nombre>` · **Ambiente:** `<prod>` · **Fecha:** `<AAAA-MM-DD>`
- **Alcance:** cuentas, regiones y servicios revisados
- **Resultado global:** `<n>` riesgos altos · `<n>` medios · `<n>` bajos

## 2. Hallazgos por pilar
| ID | Pilar | Pregunta WAF | Hallazgo | Riesgo | Evidencia |
|----|-------|--------------|----------|--------|-----------|
| SEC-01 | Seguridad | SEC 8 | Buckets sin cifrado KMS | Alto | Prowler / consola |

## 3. Plan de remediación priorizado
| Prioridad | ID | Acción | Esfuerzo | Impacto | Responsable | Fecha objetivo |
|-----------|----|--------|----------|---------|-------------|----------------|
| P1 | SEC-01 | Habilitar SSE-KMS y política deny de uploads sin cifrar | Bajo | Alto | `<equipo>` | `<fecha>` |

Criterio: **P1** = riesgo alto y esfuerzo bajo/medio (≤ 30 días); **P2** = riesgo medio (≤ 90 días); **P3** = mejora continua.

## 4. Checklist SecCheck
- [ ] IAM: MFA, sin llaves de larga duración, mínimo privilegio, Access Analyzer
- [ ] Datos: cifrado en reposo/tránsito, bloqueo público S3, backups
- [ ] Detección: CloudTrail org, GuardDuty, Config, Security Hub
- [ ] Red: segmentación, SG restrictivos, VPC endpoints, WAF
- [ ] Respuesta a incidentes: runbooks, contactos, ejercicios
- [ ] Gobierno: multicuenta, SCPs, tags, presupuestos

## 5. Herramientas de apoyo
`../scripts/seccheck.sh` (Checkov, cfn-lint, Prowler `pci_4.0_aws`) · AWS Well-Architected Tool
