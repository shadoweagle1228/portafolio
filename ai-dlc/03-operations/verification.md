# Operations: verificacion

## Checklist previo a produccion
- [ ] `pytest`, `ruff`, `mypy`, `bandit`, `pip-audit` en verde
- [ ] `checkov` sin hallazgos nuevos
- [ ] Imagen escaneada (Trivy) sin CVE criticas
- [ ] Rol IAM del servicio es de solo lectura
- [ ] Alarmas y dashboard desplegados (`observability/`)

## Runbook breve
| Sintoma | Accion |
|---------|--------|
| `/audit` responde 5xx | Revisar logs del pod y permisos IAM (IRSA) |
| Hallazgo S3-001 critico | Escalar a SecOps; bloquear acceso publico de inmediato |
