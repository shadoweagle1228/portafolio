---
name: pci-dss-iac-auditor
description: Audita plantillas CloudFormation, Terraform y CDK contra controles de seguridad PCI DSS v4.0.
metadata:
  framework: PCI-DSS-v4.0
  version: "1.0.0"
  author: Edwin
---

# PCI DSS v4.0 IaC Auditor Skill

Esta habilidad especializa al agente de IA (Kiro, Google Gemini/Antigravity) para auditar, diseñar o corregir infraestructura como código (CloudFormation, Terraform, CDK) bajo cumplimiento estricto de PCI DSS v4.0.

## 1. Principios de Validación (Reglas Inquebrantables)
Todo recurso de almacenamiento o cómputo debe satisfacer:

1. **Req. 1.4 & 7.2 (Control de Acceso y Mínimo Privilegio):**
   - Bloqueo público total (`PublicAccessBlockConfiguration` o `aws_s3_bucket_public_access_block`).
   - Propiedad de objetos forzada (`BucketOwnerEnforced`), sin uso de ACLs legacy.
2. **Req. 3.5.1 & 3.7.4 (Protección de Datos Criptográficos):**
   - Cifrado obligatorio en reposo con CMK dedicada (`aws:kms`), nunca llaves compartidas por defecto.
   - Rotación anual automática habilitada (`EnableKeyRotation = true`).
   - Políticas de llave con separación estricta de funciones (Administradores vs Usuarios vía S3).
3. **Req. 4.2.1 (Criptografía Fuerte en Tránsito):**
   - Denegación explícita si `aws:SecureTransport == false`.
   - Denegación de versiones obsoletas `s3:TlsVersion < 1.2`.
4. **Req. 10.2, 10.3 & 10.5.1 (Trazabilidad e Inmutabilidad de Auditoría):**
   - Bucket de logs con `ObjectLockConfiguration` en modo `COMPLIANCE` (retención mínima de 365 días).
   - Políticas de entrega de logs protegidas contra **Confused Deputy** mediante condición `ArnEquals: aws:SourceArn`.
   - Reglas de ciclo de vida con recuperación inmediata (`GLACIER_IR`).
   - Etiquetado de auditoría (`AuditTrail = cloudtrail-s3-data-events-required`).

## 2. Instrucciones para el Agente
- **Nunca sugerir desactivar un control de seguridad** para resolver problemas de conectividad o despliegue.
- Al evaluar políticas S3, no exigir cabeceras manuales en `PUT` si el bucket tiene KMS por defecto; usar siempre la condición `StringNotEqualsIfExists` para evitar falsos rechazos en clientes transparentes.
- Producir siempre código con arquitectura limpia, idempotente y preparado para pruebas automatizadas.
