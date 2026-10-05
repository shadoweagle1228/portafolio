# Ejemplo anonimizado de WAFR — "Cliente X, plataforma de pagos"

**Resultado:** 4 riesgos altos · 7 medios · 5 bajos (datos ficticios con fines de demostración)

| ID | Pilar | Hallazgo | Riesgo | Remediación en este repo |
|----|-------|----------|--------|--------------------------|
| SEC-01 | Seguridad | Buckets con cifrado SSE-S3 y sin política TLS | Alto | [`iac/terraform/modules/secure-s3-bucket`](../iac/terraform/modules/secure-s3-bucket) |
| SEC-02 | Seguridad | Sin SCP que impida desactivar CloudTrail | Alto | [`governance/main.tf`](../governance/main.tf) |
| REL-01 | Confiabilidad | Aplicación en una sola AZ | Alto | [`payments-ha`](../payments-ha/README.md) |
| COST-01 | Costos | Sin presupuestos ni etiquetas | Medio | [`governance/main.tf`](../governance/main.tf) |
| OPS-01 | Excelencia operativa | Despliegues manuales | Medio | [`.github/workflows`](../.github/workflows) |
| SEC-03 | Seguridad | Keycloak/IdP sin NetworkPolicy | Medio | [`k8s/keycloak`](../k8s/keycloak) |
