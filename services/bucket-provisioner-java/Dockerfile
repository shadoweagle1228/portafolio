# Stage 1: Build
FROM maven:3.9.9-eclipse-temurin-21-jammy AS build
WORKDIR /app
COPY pom.xml .
# Descargar dependencias en capa cacheable
RUN mvn -B -ntp dependency:go-offline

COPY src src
RUN mvn -B -ntp package -DskipTests

# Stage 2: Runtime ligero y seguro (Security First)
FROM eclipse-temurin:21-jre-jammy
WORKDIR /app

# Usuario no root (PCI DSS Req. 6 / Principio de mínimo privilegio)
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /sbin/nologin -M appuser

COPY --from=build --chown=appuser:appgroup /app/target/bucket-provisioner-0.1.0.jar app.jar

USER 10001

ENV JAVA_OPTS="-XX:+UseContainerSupport -XX:MaxRAMPercentage=75.0 -Dfile.encoding=UTF-8"

ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar \"$@\"", "--"]
