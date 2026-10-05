FROM quay.io/wildfly/wildfly:34.0.0.Final-jdk21
# Aplicaciones se despliegan copiando el .war a standalone/deployments
# COPY target/app.war /opt/jboss/wildfly/standalone/deployments/
USER 1000
EXPOSE 8080
CMD ["/opt/jboss/wildfly/bin/standalone.sh", "-b", "0.0.0.0"]
