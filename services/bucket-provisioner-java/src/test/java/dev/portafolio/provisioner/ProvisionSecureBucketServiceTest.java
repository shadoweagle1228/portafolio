package dev.portafolio.provisioner;

import static org.junit.jupiter.api.Assertions.*;

import dev.portafolio.provisioner.application.ProvisionSecureBucketService;
import dev.portafolio.provisioner.application.port.out.BucketGateway;
import dev.portafolio.provisioner.domain.BucketSpec;
import dev.portafolio.provisioner.domain.SecurePolicyFactory;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;

class ProvisionSecureBucketServiceTest {

    private static final String KMS = "arn:aws:kms:us-east-1:111122223333:key/abc";

    static class RecordingGateway implements BucketGateway {
        final List<String> calls = new ArrayList<>();
        public void createBucket(String b, boolean lock) { calls.add("create:" + b + ":" + lock); }
        public void blockPublicAccess(String b) { calls.add("pab:" + b); }
        public void enableKmsEncryption(String b, String k) { calls.add("kms:" + b); }
        public void enableVersioning(String b) { calls.add("ver:" + b); }
        public void enableAccessLogging(String b, String t, String p) { calls.add("log:" + b + "->" + t); }
        public void applyPolicy(String b, String p) { calls.add("policy:" + b); }
        public void applyTags(BucketSpec s, String b) { calls.add("tags:" + b); }
    }

    @Test
    void createsLogsBucketBeforeDataBucketAndAppliesAllControls() {
        var gw = new RecordingGateway();
        new ProvisionSecureBucketService(gw).provision(new BucketSpec("my-data", "dev", "team", KMS, 365));

        assertEquals("create:my-data-logs:true", gw.calls.get(0));
        assertTrue(gw.calls.indexOf("create:my-data:false") > gw.calls.indexOf("create:my-data-logs:true"));
        assertTrue(gw.calls.containsAll(List.of("pab:my-data", "kms:my-data", "ver:my-data",
                "log:my-data->my-data-logs", "policy:my-data", "tags:my-data")));
    }

    @Test
    void rejectsShortLogRetention() {
        assertThrows(IllegalArgumentException.class, () -> new BucketSpec("my-data", "dev", "team", KMS, 30));
    }

    @Test
    void rejectsInvalidBucketName() {
        assertThrows(IllegalArgumentException.class, () -> new BucketSpec("Bad_Name", "dev", "team", KMS, 365));
    }

    @Test
    void policyEnforcesTls() {
        String policy = SecurePolicyFactory.policyFor(new BucketSpec("my-data", "dev", "team", KMS, 365));
        assertTrue(policy.contains("aws:SecureTransport"));
        assertTrue(policy.contains("arn:aws:s3:::my-data/*"));
    }
}
