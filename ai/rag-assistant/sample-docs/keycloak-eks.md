# Keycloak en Kubernetes (EKS)

Keycloak se despliega con Kustomize en el namespace `keycloak` con Pod Security Standard `restricted`: ejecucion como no-root,
sistema de archivos de solo lectura, sin escalada de privilegios y todas las capabilities eliminadas.

Corre con 2 replicas minimas en produccion, un PodDisruptionBudget con `minAvailable: 1` y un HorizontalPodAutoscaler hasta 6
replicas al 70% de CPU. La red usa una NetworkPolicy de denegacion por defecto, con reglas explicitas para el ingress,
la comunicacion JGroups entre pods, DNS y la base de datos en el puerto 5432.

Los secretos de base de datos y administrador nunca se guardan en Git: se sincronizan desde AWS Secrets Manager con
External Secrets Operator.
