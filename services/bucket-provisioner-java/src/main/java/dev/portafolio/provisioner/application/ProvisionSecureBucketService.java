package dev.portafolio.provisioner.application;

import dev.portafolio.provisioner.application.port.in.ProvisionSecureBucketUseCase;
import dev.portafolio.provisioner.application.port.out.BucketGateway;
import dev.portafolio.provisioner.domain.BucketSpec;
import dev.portafolio.provisioner.domain.SecurePolicyFactory;

public class ProvisionSecureBucketService implements ProvisionSecureBucketUseCase {

    private final BucketGateway gateway;

    public ProvisionSecureBucketService(BucketGateway gateway) {
        this.gateway = gateway;
    }

    @Override
    public void provision(BucketSpec spec) {
        // 1) Bucket de logs primero: el de datos depende de el.
        String logs = spec.logsBucketName();
        gateway.createBucket(logs, true);
        gateway.blockPublicAccess(logs);
        gateway.enableVersioning(logs);
        gateway.applyTags(spec, logs);

        // 2) Bucket de datos con todos los controles antes de aceptar datos.
        String data = spec.name();
        gateway.createBucket(data, false);
        gateway.blockPublicAccess(data);
        gateway.enableKmsEncryption(data, spec.kmsKeyArn());
        gateway.enableVersioning(data);
        gateway.enableAccessLogging(data, logs, data + "/");
        gateway.applyPolicy(data, SecurePolicyFactory.policyFor(spec));
        gateway.applyTags(spec, data);
    }
}
