# Arquitectura

## Hexagonal (servicios Java y Python)
```mermaid
flowchart LR
  subgraph Adaptadores de entrada
    API[REST / CLI]
  end
  subgraph Aplicación
    UC[Casos de uso]
  end
  subgraph Dominio
    D[Entidades, value objects, reglas PCI]
  end
  subgraph Adaptadores de salida
    S3[AWS SDK S3 / KMS]
  end
  API --> UC --> D
  UC -->|puertos| S3
```
**Regla de dependencia:** las flechas solo apuntan hacia el dominio. El dominio no conoce frameworks ni AWS.

## Despliegue
```mermaid
flowchart TD
  Dev[Commit / PR] --> CI[CI: tests + SAST + SCA + Checkov]
  CI -->|OIDC, sin llaves| Deploy[Terraform / CDK / CFN]
  Deploy --> AWS[(S3 + KMS + Logs inmutables)]
  Deploy --> EKS[EKS privado] --> KC[Keycloak HA]
  AWS --> Mon[CloudWatch / Datadog / Grafana]
```

## Well-Architected: cómo se refleja cada pilar
| Pilar | Evidencia |
|-------|-----------|
| Excelencia operativa | IaC, pipelines, runbook AI-DLC, dashboards |
| Seguridad | KMS, TLS, Object Lock, OIDC, NetworkPolicy, PSS restricted |
| Confiabilidad | Versionado, réplicas + PDB + HPA, topology spread |
| Eficiencia de rendimiento | Bucket Keys, HPA, contenedores slim |
| Optimización de costos | Lifecycle a Glacier, expiración de versiones, tags de costo |
| Sostenibilidad | Autoescalado, imágenes mínimas, lifecycle de datos |
