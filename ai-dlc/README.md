# AI-DLC (AI-Driven Development Lifecycle) & Casos Prácticos con IA

Este documento describe la metodología **AI-DLC** aplicada en este portafolio, demostrando cómo la integración sistemática de agentes de Inteligencia Artificial (Kiro, Google Suite / Gemini, Antigravity) acelera el ciclo de ingeniería manteniendo **cero degradación técnica y seguridad estricta**.

---

## 1. El Problema Resuelto: Respuestas Perdidas y Alucinaciones

### ¿Qué ocurría antes?
- **Respuestas Perdidas / Bucles Incompletos:** Los asistentes solían quedarse en estados como *"estoy analizando la información..."* o consumían el contexto sin emitir una solución técnica concreta.
- **Alucinaciones en Arquitectura:** Generación de parámetros obsoletos o no soportados de CloudFormation/Terraform, y respuestas inventadas ante vacíos de contexto.

### ¿Cómo se eliminó con AI-DLC?
1. **Garantía Estructural de Respuesta (Anti-Drop):**
   - En la arquitectura del software asistido por IA (`ai/rag-assistant`), el caso de uso `AnswerQuestion` está encapsulado para garantizar siempre un objeto `Answer` tipado (`answered`, `no_context`, `invalid`, `error`). Nunca deja colgado al cliente.
2. **Filtrado por Umbral de Similitud (Anti-Alucinación por RAG):**
   - Antes de llamar a los modelos fundacionales, el motor evalúa la relevancia semántica de los fragmentos recuperados (`min_score = 0.3`).
   - Si no hay evidencia documental suficiente, el sistema responde explícitamente con honestidad técnica (`no_context`) en lugar de permitir que el LLM invente hechos.
3. **Guardrails de Datos Sensibles:**
   - Amazon Bedrock Guardrail configurado para bloquear números de tarjeta (PAN), CVVs, llaves de API o contraseñas en cualquier interacción.

---

## 2. Ecosistema de Agentes: Skills y Model Context Protocol (MCP)

### A. Skills Especializadas (`ai/skills/`)
Definiciones declarativas de capacidades para herramientas como Kiro o Gemini Code Assist:
- [`pci-dss-iac-auditor`](skills/pci-dss-iac-auditor/SKILL.md): Imbuye en el agente las directrices inquebrantables de PCI DSS v4.0 (bloqueo público, cifrado KMS con rotación, `GLACIER_IR`, prevención de Confused Deputy).
- [`well-architected-reviewer`](skills/well-architected-reviewer/SKILL.md): Estandariza la realización de revisiones WAFR y SecCheck clasificando hallazgos por severidad de negocio (P1, P2, P3).

### B. Servidor MCP de Auditoría (`ai/mcp-server/`)
Servidor bajo el estándar **Model Context Protocol** (JSON-RPC) que expone herramientas de sólo lectura a los agentes:
- `audit_single_bucket`: Consulta la postura de un bucket S3.
- `audit_all_buckets`: Realiza un escaneo transversal de la cuenta AWS.

---

## 3. Asistente RAG Efímero (`ai/rag-assistant/`)
- Diseñado con **Arquitectura Hexagonal**.
- Aprovisionable y destruible en minutos vía **AWS CDK** (`cdk deploy` / `cdk destroy`).
- 100% Serverless y pago por uso: Sin costos fijos de clústeres vectoriales ni endpoints permanentes.

---

## 4. Bitácora de Decisiones AI-DLC en este Repositorio

| Evento | Propuesta de la IA | Decisión y Validación Humana | Resultado |
|---|---|---|---|
| **Política de Cifrado S3** | Eliminar completamente el bloque `DenyUnencryptedUploads`. | **Rechazada y ajustada:** Se transformó en `DenyExplicitNonKmsEncryption` con `StringNotEqualsIfExists` para permitir subidas transparentes pero bloquear SSE-S3 manual. | Aceptada con hardening |
| **Recuperación de Logs PCI** | Mantener transición tradicional a `GLACIER`. | **Ajustada:** Se cambió a `GLACIER_INSTANT_RETRIEVAL` para cumplir con el Req. 10.5.1 (disponibilidad inmediata en milisegundos durante 12 meses). | Aceptada con optimización |
| **Separación de KMS** | Conceder `kms:*` al root de la cuenta. | **Rechazada:** Se dividió en roles independientes de Administradores y Usuarios vía S3 (Req. 7 de mínimo privilegio). | Aceptada con mínimo privilegio |
| **Dependencia Circular en CDK** | Intentar forzar dependencia directa del bucket al bucket policy. | **Detectada por pruebas y corregida:** Se desacopló la dependencia circular permitiendo síntesis limpia y despliegue idempotente. | Aceptada tras fix |
