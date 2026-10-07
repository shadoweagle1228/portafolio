# Guía de Despliegue y Destrucción: RAG Assistant Efímero (AWS CDK)

Este stack está diseñado con mentalidad **100% On-Demand / Pay-as-you-go** para tu cuenta personal de AWS:
- **Sin costos fijos**: No usa clústeres OpenSearch administrados, ni NAT Gateways, ni instancias EC2 encendidas.
- **Desplegable y destructible al instante**: Todos los recursos (Buckets S3 con auto-delete, grupos CloudWatch Logs, Lambda y Guardrails) tienen `RemovalPolicy.DESTROY`.

---

## 1. Prerrequisitos
- AWS CLI configurado con credenciales (`aws sts get-caller-identity`).
- Node.js instalado (para la CLI de CDK).
- Modelos habilitados en **Amazon Bedrock** (Consola AWS $\rightarrow$ Bedrock $\rightarrow$ Model Access en `us-east-1`):
  - `amazon.titan-embed-text-v2:0` (Embeddings)
  - `amazon.nova-lite-v1:0` o `anthropic.claude-3-haiku-20240307-v1:0` (Generación)

---

## 2. Despliegue en tu cuenta

```bash
cd ai/rag-assistant/cdk

# 1. Instalar dependencias
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 2. Desplegar con límite de presupuesto de seguridad ($5 USD)
cdk deploy -c budget_email=tu-correo@ejemplo.com
```

Al terminar, el stack emitirá en la consola:
- `KnowledgeBucketName`: Bucket S3 donde residen los documentos de conocimiento.
- `IngestFunctionName`: Nombre de la función Lambda de indexación.
- `QueryFunctionName`: Nombre de la función Lambda de consultas.

---

## 3. Uso y Prueba

### Paso A: Indexar documentos
Ejecuta la Lambda de ingesta para procesar los documentos de muestra (`sample-docs/`) y crear el índice vectorial:
```bash
aws lambda invoke \
  --function-name <IngestFunctionName> \
  response-ingest.json
cat response-ingest.json
```

### Paso B: Consultar al asistente
Haz una pregunta técnica sobre tus políticas o arquitectura:
```bash
aws lambda invoke \
  --function-name <QueryFunctionName> \
  --cli-binary-format raw-in-base64-out \
  --payload '{"question": "¿Cuál es la política de cifrado de S3 y cómo se protegen las llaves?"}' \
  response-query.json

cat response-query.json
```

**Resultado esperado:**
- `status`: `"answered"`
- `answer`: Respuesta fundamentada citando `[politica-cifrado-s3.md]`.
- `sources`: `["politica-cifrado-s3.md"]`

**Prueba de Anti-Alucinación (Pregunta fuera de contexto):**
```bash
aws lambda invoke \
  --function-name <QueryFunctionName> \
  --cli-binary-format raw-in-base64-out \
  --payload '{"question": "¿Cómo se prepara un pastel de chocolate?"}' \
  response-query.json

cat response-query.json
```
**Resultado esperado:**
- `status`: `"no_context"`
- `answer`: `"No tengo informacion suficiente en la base de conocimiento para responder eso."` *(Cero alucinaciones, el modelo no es invocado innecesariamente)*.

---

## 4. Destrucción Total (Limpieza inmediata)

Cuando termines tu demostración o pruebas, elimina todo con un solo comando sin dejar recursos huérfanos ni facturación residual:

```bash
cdk destroy
```
Confirma con `y` y AWS CDK purgará automáticamente el bucket S3, las funciones Lambda, los CloudWatch Log Groups y el Guardrail de Bedrock.
