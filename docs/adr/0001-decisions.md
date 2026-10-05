# ADR-0001: Arquitectura hexagonal en los servicios

- **Estado:** Aceptada
- **Contexto:** Las reglas de cumplimiento cambian (PCI DSS v4.x) y la infraestructura (AWS SDK, frameworks) evoluciona a otro ritmo.
- **Decisión:** Dominio puro, casos de uso y puertos en el centro; AWS y HTTP/CLI como adaptadores intercambiables.
- **Consecuencias:** (+) pruebas rápidas con fakes, sin AWS. (+) cambio de framework sin tocar reglas. (−) más archivos/boilerplate.

# ADR-0002: Un mismo caso de uso en CloudFormation, Terraform y CDK
- **Estado:** Aceptada
- **Decisión:** Implementar el bucket seguro con las tres herramientas y un único mapeo PCI para comparar enfoques.
- **Consecuencias:** Demuestra dominio de las tres; implica mantener paridad (verificada con Checkov/cdk-nag).

# ADR-0003: Autenticación de pipelines vía OIDC
- **Estado:** Aceptada
- **Decisión:** GitHub Actions y Bitbucket asumen roles IAM por OIDC; prohibidas las access keys estáticas (PCI DSS 8.3/8.6).
