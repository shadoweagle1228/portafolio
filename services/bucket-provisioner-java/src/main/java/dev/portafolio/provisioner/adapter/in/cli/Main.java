package dev.portafolio.provisioner.adapter.in.cli;

import dev.portafolio.provisioner.adapter.out.aws.S3BucketGateway;
import dev.portafolio.provisioner.application.ProvisionSecureBucketService;
import dev.portafolio.provisioner.domain.BucketSpec;
import software.amazon.awssdk.services.s3.S3Client;

/** Adaptador de entrada (CLI) y composition root. Uso: Main <bucket> <env> <owner> <kmsArn>. */
public final class Main {

    private Main() {}

    public static void main(String[] args) {
        if (args.length != 4) {
            System.err.println("Uso: Main <bucket> <dev|qa|prod> <owner> <kmsKeyArn>");
            System.exit(2);
        }
        var spec = new BucketSpec(args[0], args[1], args[2], args[3], BucketSpec.PCI_MIN_LOG_RETENTION_DAYS);
        try (S3Client s3 = S3Client.create()) {
            new ProvisionSecureBucketService(new S3BucketGateway(s3)).provision(spec);
            System.out.println("Bucket aprovisionado: " + spec.name());
        }
    }
}
