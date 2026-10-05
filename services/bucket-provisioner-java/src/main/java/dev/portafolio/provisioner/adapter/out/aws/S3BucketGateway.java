package dev.portafolio.provisioner.adapter.out.aws;

import dev.portafolio.provisioner.application.port.out.BucketGateway;
import dev.portafolio.provisioner.domain.BucketSpec;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.model.*;

/** Adaptador de salida: implementa el puerto con AWS SDK v2. */
public class S3BucketGateway implements BucketGateway {

    private final S3Client s3;

    public S3BucketGateway(S3Client s3) {
        this.s3 = s3;
    }

    @Override
    public void createBucket(String bucketName, boolean objectLock) {
        s3.createBucket(CreateBucketRequest.builder()
                .bucket(bucketName)
                .objectLockEnabledForBucket(objectLock)
                .objectOwnership(ObjectOwnership.BUCKET_OWNER_ENFORCED)
                .build());
    }

    @Override
    public void blockPublicAccess(String bucketName) {
        s3.putPublicAccessBlock(PutPublicAccessBlockRequest.builder()
                .bucket(bucketName)
                .publicAccessBlockConfiguration(PublicAccessBlockConfiguration.builder()
                        .blockPublicAcls(true).blockPublicPolicy(true)
                        .ignorePublicAcls(true).restrictPublicBuckets(true).build())
                .build());
    }

    @Override
    public void enableKmsEncryption(String bucketName, String kmsKeyArn) {
        s3.putBucketEncryption(PutBucketEncryptionRequest.builder()
                .bucket(bucketName)
                .serverSideEncryptionConfiguration(ServerSideEncryptionConfiguration.builder()
                        .rules(ServerSideEncryptionRule.builder()
                                .bucketKeyEnabled(true)
                                .applyServerSideEncryptionByDefault(ServerSideEncryptionByDefault.builder()
                                        .sseAlgorithm(ServerSideEncryption.AWS_KMS)
                                        .kmsMasterKeyID(kmsKeyArn).build())
                                .build())
                        .build())
                .build());
    }

    @Override
    public void enableVersioning(String bucketName) {
        s3.putBucketVersioning(PutBucketVersioningRequest.builder()
                .bucket(bucketName)
                .versioningConfiguration(VersioningConfiguration.builder()
                        .status(BucketVersioningStatus.ENABLED).build())
                .build());
    }

    @Override
    public void enableAccessLogging(String bucketName, String targetBucket, String prefix) {
        s3.putBucketLogging(PutBucketLoggingRequest.builder()
                .bucket(bucketName)
                .bucketLoggingStatus(BucketLoggingStatus.builder()
                        .loggingEnabled(LoggingEnabled.builder()
                                .targetBucket(targetBucket).targetPrefix(prefix).build())
                        .build())
                .build());
    }

    @Override
    public void applyPolicy(String bucketName, String policyJson) {
        s3.putBucketPolicy(PutBucketPolicyRequest.builder().bucket(bucketName).policy(policyJson).build());
    }

    @Override
    public void applyTags(BucketSpec spec, String bucketName) {
        s3.putBucketTagging(PutBucketTaggingRequest.builder()
                .bucket(bucketName)
                .tagging(Tagging.builder().tagSet(
                        Tag.builder().key("Environment").value(spec.environment()).build(),
                        Tag.builder().key("Owner").value(spec.owner()).build(),
                        Tag.builder().key("Compliance").value("pci-dss-v4").build()).build())
                .build());
    }
}
