# Portafolio de Ingeniería Cloud — Secure-by-Design

Repositorio que demuestra, con un **caso de uso único** (almacenamiento S3 conforme a **PCI DSS v4.0**),
la trayectoria profesional en arquitectura cloud, IaC, CI/CD, Kubernetes, desarrollo Java/Python y AI-DLC.

> Principios: **Security First** · **Arquitectura hexagonal** · **Clean Code** · **IaC reproducible** · **Todo probado y escaneado en CI**

## Mapa del repositorio

| Carpeta | Contenido | Habilidad demostrada |
|---------|-----------|----------------------|
| [`iac/cloudformation`](iac/cloudformation) | Template de bucket S3 + KMS + logs inmutables | CloudFormation |
| [`iac/terraform`](iac/terraform) | Módulo `secure-s3-bucket`, entornos dev/prod, cluster EKS privado | Terraform, EKS |
| [`iac/cdk`](iac/cdk) | Construct `SecureBucket` (Python) + tests + cdk-nag | AWS CDK |
| [`services/bucket-auditor-python`](services/bucket-auditor-python) | Auditor PCI de buckets (FastAPI, hexagonal) | Python |
| [`services/bucket-provisioner-java`](services/bucket-provisioner-java) | Aprovisionador de buckets seguros (hexagonal, AWS SDK v2) | Java |
| [`k8s/keycloak`](k8s/keycloak) | Keycloak HA con Kustomize, NetworkPolicy, ExternalSecrets, PSS restricted | Kubernetes |
| [`.github/workflows`](.github/workflows) | CI + deploy con OIDC | GitHub Actions |
| [`bitbucket-pipelines.yml`](bitbucket-pipelines.yml) | CI + deploy dev/prod con OIDC | Bitbucket Pipelines |
| [`Jenkinsfile`](Jenkinsfile) | Build, SonarQube, Selenium, aprobación | Jenkins |
| [`observability`](observability) | Alarmas CloudWatch, monitor Datadog, dashboard Grafana | Monitoreo |
| [`security`](security) · [`scripts/seccheck.sh`](scripts/seccheck.sh) | Checkov, cfn-lint, Prowler PCI 4.0 | SecCheck / WAFR |
| [`ai-dlc`](ai-dlc) | Ejemplo completo Inception → Construction → Operations | AI-DLC |
| [`governance`](governance) | SCPs, tag policy, Budgets, reglas AWS Config | Gobierno y control de costos |
| [`landing-zone`](landing-zone) | Organizations (OUs/cuentas), CloudTrail org inmutable, GuardDuty | Multicuenta |
| [`wafr`](wafr) | Plantilla de reporte WAFR/SecCheck + ejemplo anonimizado | Well-Architected / SecCheck |
| [`payments-ha`](payments-ha) | Arquitectura de referencia de pagos HA + SQS FIFO/DLQ | Alta disponibilidad |
| [`k8s/addons`](k8s/addons) | Karpenter, Kyverno, Argo CD (GitOps) | EKS avanzado |
| [`migration/svn-to-git`](migration/svn-to-git) | Script y guía de migración | SVN → Git |
| [`legacy-appservers`](legacy-appservers) | WildFly + LDAP en contenedores endurecidos | Servidores de aplicaciones |
| [`cost-optimization`](cost-optimization) | Detector de desperdicio y tagging (con tests) | FinOps |
| [`docs`](docs) | Mapeo PCI DSS v4, ADRs, arquitectura, roadmap | Documentación |

## Un mismo requisito, tres implementaciones
El bucket seguro se implementa en **CloudFormation, Terraform y CDK** con los mismos controles
([mapeo PCI DSS](docs/pci-dss-mapping.md)): CMK con rotación, TLS 1.2+, bloqueo público, versionado,
logs inmutables (Object Lock COMPLIANCE, 365 días) y tags de clasificación.

## Inicio rápido

```bash
# Python
cd services/bucket-auditor-python && pip install -e ".[dev]" && pytest

# Java
cd services/bucket-provisioner-java && mvn verify

# CDK (con cdk-nag)
cd iac/cdk && pip install -r requirements.txt && pytest && cdk synth

# Terraform
cd iac/terraform/envs/dev && terraform init -backend=false && terraform validate

# CloudFormation
./scripts/deploy-cfn.sh dev

# Escaneos de seguridad
./scripts/seccheck.sh
```

## Documentación
- [Arquitectura](docs/architecture.md) · [ADRs](docs/adr) · [Mapeo PCI DSS v4](docs/pci-dss-mapping.md) · [Roadmap](docs/roadmap.md)

> ⚠️ Los nombres de bucket, IDs de cuenta y dominios son ejemplos. Ningún secreto vive en este repositorio.
> El mapeo PCI DSS es ilustrativo y no sustituye una evaluación por un QSA.
