# Bitacora de decisiones IA / validacion humana

| Fecha | Decision propuesta por la IA | Validacion humana | Resultado |
|-------|------------------------------|-------------------|-----------|
| 2026-10-04 | Dominio con funcion pura `evaluate()` | Aprobada: facilita pruebas sin AWS | Aceptada |
| 2026-10-04 | Usar `Protocol` para el puerto | Aprobada: tipado estructural sin herencia | Aceptada |
| 2026-10-04 | Marcar `kms_rotation_enabled=None` como "desconocido" y no como fallo | Ajustada: evita falsos positivos con llaves AWS-managed | Modificada |
