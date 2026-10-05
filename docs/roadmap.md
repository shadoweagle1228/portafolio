# Roadmap: qué más agregar según tu CV

| Prioridad | Módulo | Respalda este logro del CV |
|-----------|--------|----------------------------|
| Alta | `governance/`: AWS Organizations, SCPs (deny public S3, regiones permitidas), tag policies, Budgets, Config conformance pack PCI | Modelos de gobierno multicuenta, control de costos |
| Alta | `wafr/`: plantilla de reporte WAFR/SecCheck (hallazgos, riesgo, plan de remediación) + ejemplo anonimizado | WAFR y SecCheck para clientes |
| Alta | `landing-zone/` (Control Tower / Terraform): cuentas, SSO, CloudTrail org, GuardDuty | Gobierno multicuenta |
| Media | `payments-ha/`: arquitectura de referencia multi-AZ/multi-región para pagos (Route 53, Aurora Global, SQS) — **sin datos confidenciales de Bre-B** | Bre-B / alta disponibilidad |
| Media | `eks/addons`: Karpenter, AWS LB Controller, External Secrets, Kyverno, Argo CD (GitOps) | EKS con autoescalado |
| Media | `migration/svn-to-git/`: script y guía de migración con `git svn` y validación | Migración SVN → Git |
| Media | `legacy-appservers/`: Ansible/Docker para WildFly (+LDAP) como referencia de modernización | WebSphere/WildFly/LDAP |
| Baja | `cost-optimization/`: scripts de recursos huérfanos, Savings Plans, tagging compliance | Control de costos |
| Baja | PHP: pequeño ejemplo histórico (opcional, no aporta al perfil actual) | 404 Creativo |

> ⚠️ Confidencialidad: no publiques información de clientes (Bre-B, etc.). Usa arquitecturas de referencia genéricas.

## Recomendaciones para el CV
- Cuantifica resultados (p. ej. "reduje tiempo de despliegue de X a Y").
- Elimina la viñeta duplicada de Java en Heinsohn (Arquitecto de Soluciones).
- Añade certificaciones (AWS SA Pro/Security Specialty, CKA) y enlaza este repositorio.
- Corrige tiempos verbales: "Diseñé", "Estandaricé", "Actué".
