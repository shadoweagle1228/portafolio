package dev.portafolio.provisioner.domain;

import java.util.regex.Pattern;

/** Value object inmutable; valida invariantes de negocio al construirse. */
public record BucketSpec(String name, String environment, String owner, String kmsKeyArn, int logRetentionDays) {

    public static final int PCI_MIN_LOG_RETENTION_DAYS = 365; // Req. 10.5.1
    private static final Pattern NAME = Pattern.compile("^[a-z0-9][a-z0-9.-]{2,62}$");

    public BucketSpec {
        if (name == null || !NAME.matcher(name).matches()) {
            throw new IllegalArgumentException("Nombre de bucket invalido: " + name);
        }
        if (!java.util.Set.of("dev", "qa", "prod").contains(environment)) {
            throw new IllegalArgumentException("Ambiente invalido: " + environment);
        }
        if (owner == null || owner.isBlank()) {
            throw new IllegalArgumentException("owner es obligatorio (tagging)");
        }
        if (kmsKeyArn == null || !kmsKeyArn.startsWith("arn:")) {
            throw new IllegalArgumentException("Se requiere una CMK de KMS (Req. 3.5)");
        }
        if (logRetentionDays < PCI_MIN_LOG_RETENTION_DAYS) {
            throw new IllegalArgumentException("PCI DSS 10.5.1 exige >= 365 dias de retencion");
        }
    }

    public String logsBucketName() {
        return name + "-logs";
    }
}
