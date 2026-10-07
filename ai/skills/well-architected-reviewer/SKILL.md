---
name: well-architected-reviewer
description: Conduce evaluaciones Well-Architected Framework Reviews (WAFR) y SecCheck con planes de remediación priorizados.
metadata:
  framework: AWS-WAFR-SecCheck
  version: "1.0.0"
  author: Edwin
---

# AWS Well-Architected & SecCheck Reviewer Skill

Especializa al agente para realizar revisiones de arquitectura técnica bajo los 6 pilares de AWS Well-Architected Framework y evaluaciones profundas de seguridad (SecCheck).

## 1. Criterio de Priorización de Remediaciones
Toda recomendación generada por el agente debe estar categorizada con este marco:

- **P1 (Crítica / Urgente):**
  - Brecha de seguridad directa (acceso público indebido, llaves expuestas, falta de MFA/cifrado).
  - Tiempo estimado de mitigación: $\le$ 30 días.
- **P2 (Media):**
  - Falta de alta disponibilidad multi-AZ, retención subóptima de logs, acoplamiento síncrono crítico.
  - Tiempo estimado de mitigación: $\le$ 90 días.
- **P3 (Mejora Continua):**
  - Oportunidades de optimización de costos (FinOps) o refactorización para adopción serverless.

## 2. Formato de Salida Obligatorio
Cada hallazgo debe presentarse con:
1. **Identificador & Pilar:** (e.g. `SEC-01`, Seguridad / Confiabilidad).
2. **Impacto en el Negocio:** Consecuencia operativa y financiera.
3. **Control Well-Architected asociado:** (e.g., `SEC 8: Protect data at rest`).
4. **Acción de Remediación Técnica:** Código IaC o comando CLI específico.
