# AI-DLC: Caso de ejemplo — "Secure Bucket Auditor"

Este directorio muestra el flujo de **AI-Driven Development Lifecycle (AI-DLC)** aplicado a una funcionalidad
real del repo. El principio: la IA propone, el humano valida en cada compuerta ("human in the loop").

## Fases y artefactos

| Fase | Artefacto | Rol IA | Rol humano |
|------|-----------|--------|------------|
| Inception | [`01-inception/intent-and-user-stories.md`](01-inception/intent-and-user-stories.md) | Descompone el intent en historias y unidades de trabajo | Valida alcance y prioridades |
| Construction | [`02-construction/design-and-tasks.md`](02-construction/design-and-tasks.md) | Propone modelo de dominio, puertos y plan de tareas | Revisa arquitectura (hexagonal) y seguridad |
| Construction | `services/bucket-auditor-python/` | Genera codigo y tests por tarea | Code review + ejecucion de tests |
| Operations | [`03-operations/verification.md`](03-operations/verification.md) | Redacta checklist y runbook | Aprueba y despliega |

## Reglas de trabajo con agentes (ver [`audit.md`](audit.md))
1. Toda decision de la IA queda registrada con su validacion humana.
2. Ningun cambio pasa sin pruebas automaticas ni escaneos de seguridad (Checkov, Bandit, pip-audit).
3. El agente nunca recibe secretos ni datos reales de tarjetahabiente.
