# Inception

## Intent
> Como equipo de plataforma necesitamos **detectar automaticamente** buckets S3 que incumplan PCI DSS v4.0
> para reducir el riesgo en el CDE (entorno de datos de tarjetahabiente) sin revisiones manuales.

## Historias de usuario
| ID | Historia | Criterios de aceptacion |
|----|----------|-------------------------|
| US-1 | Como auditor quiero consultar el estado de un bucket | Devuelve hallazgos con regla, requisito PCI y severidad |
| US-2 | Como SecOps quiero auditar todos los buckets de la cuenta | Lista de reportes; error de un bucket no detiene el resto |
| US-3 | Como arquitecto quiero que el servicio sea de solo lectura | Rol IAM con unicamente `s3:Get*`, `s3:List*`, `kms:GetKeyRotationStatus` |

## Unidades de trabajo
1. **Dominio**: reglas de evaluacion (S3-001..S3-006).
2. **Aplicacion**: casos de uso `AuditBucket`, `AuditAllBuckets`.
3. **Adaptadores**: boto3 (salida) y FastAPI (entrada).
4. **Entrega**: contenedor non-root, pipeline y despliegue en EKS.

## Riesgos / supuestos
- Las reglas cubren un subconjunto de PCI DSS; no sustituye una evaluacion QSA.
- Cuentas multiples: fuera de alcance de esta iteracion (ver backlog).
