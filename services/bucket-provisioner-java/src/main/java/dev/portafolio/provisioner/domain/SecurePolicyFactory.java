package dev.portafolio.provisioner.domain;

/** Servicio de dominio: genera la bucket policy PCI DSS (deny-by-default). */
public final class SecurePolicyFactory {

    private SecurePolicyFactory() {}

    public static String policyFor(BucketSpec spec) {
        String arn = "arn:aws:s3:::" + spec.name();
        return """
            {
              "Version": "2012-10-17",
              "Statement": [
                {
                  "Sid": "DenyInsecureTransport",
                  "Effect": "Deny",
                  "Principal": "*",
                  "Action": "s3:*",
                  "Resource": ["%1$s", "%1$s/*"],
                  "Condition": {"Bool": {"aws:SecureTransport": "false"}}
                },
                {
                  "Sid": "DenyOldTLS",
                  "Effect": "Deny",
                  "Principal": "*",
                  "Action": "s3:*",
                  "Resource": ["%1$s", "%1$s/*"],
                  "Condition": {"NumericLessThan": {"s3:TlsVersion": "1.2"}}
                },
                {
                  "Sid": "DenyUnencryptedUploads",
                  "Effect": "Deny",
                  "Principal": "*",
                  "Action": "s3:PutObject",
                  "Resource": "%1$s/*",
                  "Condition": {"StringNotEqualsIfExists": {"s3:x-amz-server-side-encryption": "aws:kms"}}
                }
              ]
            }
            """.formatted(arn);
    }
}
