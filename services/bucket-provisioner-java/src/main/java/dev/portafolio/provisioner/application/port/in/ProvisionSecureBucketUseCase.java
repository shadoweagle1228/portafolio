package dev.portafolio.provisioner.application.port.in;

import dev.portafolio.provisioner.domain.BucketSpec;

/** Puerto de entrada (caso de uso). */
public interface ProvisionSecureBucketUseCase {
    void provision(BucketSpec spec);
}
