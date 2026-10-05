package dev.portafolio.provisioner.application.port.out;

import dev.portafolio.provisioner.domain.BucketSpec;

/** Puerto de salida: lo que la aplicacion necesita de la infraestructura. */
public interface BucketGateway {

    void createBucket(String bucketName, boolean objectLock);

    void blockPublicAccess(String bucketName);

    void enableKmsEncryption(String bucketName, String kmsKeyArn);

    void enableVersioning(String bucketName);

    void enableAccessLogging(String bucketName, String targetBucket, String prefix);

    void applyPolicy(String bucketName, String policyJson);

    void applyTags(BucketSpec spec, String bucketName);
}
