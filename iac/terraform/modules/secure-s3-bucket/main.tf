locals {
  tags = merge(var.tags, {
    Environment        = var.environment
    DataClassification = var.data_classification
    Owner              = var.owner
    Compliance         = "pci-dss-v4"
    # Req. 10.2: debe estar cubierto por CloudTrail data events
    AuditTrail = "cloudtrail-s3-data-events-required"
  })
}

data "aws_caller_identity" "current" {}
data "aws_partition" "current" {}
data "aws_region" "current" {}

# ---------- KMS: privilegio minimo, separacion de funciones (Req. 7 / 3.6-3.7) ----------
# Sin kms:* para root: los administradores conservan kms:PutKeyPolicy para evitar el bloqueo de la llave.
data "aws_iam_policy_document" "kms" {
  statement {
    sid    = "KeyAdministrators"
    effect = "Allow"
    actions = [
      "kms:Create*", "kms:Describe*", "kms:Enable*", "kms:List*", "kms:Put*", "kms:Update*",
      "kms:Revoke*", "kms:Disable*", "kms:Get*", "kms:Delete*", "kms:TagResource",
      "kms:UntagResource", "kms:ScheduleKeyDeletion", "kms:CancelKeyDeletion",
    ]
    resources = ["*"]
    principals {
      type        = "AWS"
      identifiers = var.key_admin_role_arns
    }
  }

  statement {
    sid    = "KeyUsersViaS3Only"
    effect = "Allow"
    actions = [
      "kms:Encrypt", "kms:Decrypt", "kms:ReEncrypt*", "kms:GenerateDataKey*", "kms:DescribeKey",
    ]
    resources = ["*"]
    principals {
      type        = "AWS"
      identifiers = var.key_user_role_arns
    }
    condition {
      test     = "StringEquals"
      variable = "kms:ViaService"
      values   = ["s3.${data.aws_region.current.name}.amazonaws.com"]
    }
    condition {
      test     = "StringEquals"
      variable = "kms:CallerAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }
}

resource "aws_kms_key" "data" {
  description             = "CMK para ${var.bucket_name}"
  enable_key_rotation     = true
  deletion_window_in_days = 30
  policy                  = data.aws_iam_policy_document.kms.json
  tags                    = local.tags
}

resource "aws_kms_alias" "data" {
  name          = "alias/${var.bucket_name}"
  target_key_id = aws_kms_key.data.key_id
}

# ---------- Bucket de logs inmutable (Req. 10.3 / 10.5.1) ----------
resource "aws_s3_bucket" "logs" {
  bucket              = "${var.bucket_name}-logs"
  object_lock_enabled = true
  tags                = local.tags
  lifecycle { prevent_destroy = true }
}

resource "aws_s3_bucket_object_lock_configuration" "logs" {
  bucket = aws_s3_bucket.logs.id
  rule {
    default_retention {
      mode = "COMPLIANCE"
      days = var.log_retention_days
    }
  }
  depends_on = [aws_s3_bucket_versioning.logs]
}

resource "aws_s3_bucket_versioning" "logs" {
  bucket = aws_s3_bucket.logs.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "logs" {
  bucket = aws_s3_bucket.logs.id
  rule {
    apply_server_side_encryption_by_default { sse_algorithm = "AES256" }
  }
}

resource "aws_s3_bucket_ownership_controls" "logs" {
  bucket = aws_s3_bucket.logs.id
  rule { object_ownership = "BucketOwnerEnforced" }
}

resource "aws_s3_bucket_public_access_block" "logs" {
  bucket                  = aws_s3_bucket.logs.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "logs" {
  bucket = aws_s3_bucket.logs.id
  rule {
    id     = "archive-instant-retrieval-after-90-days"
    status = "Enabled"
    filter {}
    # Glacier Instant Retrieval: acceso en milisegundos durante los 12 meses (Req. 10.5.1)
    transition {
      days          = 90
      storage_class = "GLACIER_IR"
    }
  }
  depends_on = [aws_s3_bucket_versioning.logs]
}

data "aws_iam_policy_document" "logs" {
  statement {
    sid       = "DenyInsecureTransport"
    effect    = "Deny"
    actions   = ["s3:*"]
    resources = [aws_s3_bucket.logs.arn, "${aws_s3_bucket.logs.arn}/*"]
    principals {
      type        = "*"
      identifiers = ["*"]
    }
    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
  # Confused deputy: solo el bucket de datos puede entregar logs aqui.
  # El ARN se construye con el nombre (no con el recurso) para evitar dependencia circular.
  statement {
    sid       = "AllowS3ServerAccessLogsFromDataBucketOnly"
    actions   = ["s3:PutObject"]
    resources = ["${aws_s3_bucket.logs.arn}/*"]
    principals {
      type        = "Service"
      identifiers = ["logging.s3.amazonaws.com"]
    }
    condition {
      test     = "ArnEquals"
      variable = "aws:SourceArn"
      values   = ["arn:${data.aws_partition.current.partition}:s3:::${var.bucket_name}"]
    }
    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }
}

resource "aws_s3_bucket_policy" "logs" {
  bucket     = aws_s3_bucket.logs.id
  policy     = data.aws_iam_policy_document.logs.json
  depends_on = [aws_s3_bucket_public_access_block.logs]
}

# ---------- Bucket de datos ----------
resource "aws_s3_bucket" "data" {
  bucket        = var.bucket_name
  force_destroy = var.environment != "prod"
  tags          = local.tags
}

resource "aws_s3_bucket_ownership_controls" "data" {
  bucket = aws_s3_bucket.data.id
  rule { object_ownership = "BucketOwnerEnforced" }
}

resource "aws_s3_bucket_public_access_block" "data" {
  bucket                  = aws_s3_bucket.data.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "data" {
  bucket = aws_s3_bucket.data.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data" {
  bucket = aws_s3_bucket.data.id
  rule {
    bucket_key_enabled = true
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.data.arn
    }
  }
}

resource "aws_s3_bucket_logging" "data" {
  bucket        = aws_s3_bucket.data.id
  target_bucket = aws_s3_bucket.logs.id
  target_prefix = "${var.bucket_name}/"
  # El destino debe autorizar la entrega antes de habilitar el logging
  depends_on = [aws_s3_bucket_policy.logs]
}

resource "aws_s3_bucket_lifecycle_configuration" "data" {
  bucket = aws_s3_bucket.data.id
  rule {
    id     = "expire-noncurrent"
    status = "Enabled"
    filter {}
    noncurrent_version_expiration { noncurrent_days = 365 }
    abort_incomplete_multipart_upload { days_after_initiation = 7 }
  }
  depends_on = [aws_s3_bucket_versioning.data]
}

data "aws_iam_policy_document" "data" {
  statement {
    sid       = "DenyInsecureTransport"
    effect    = "Deny"
    actions   = ["s3:*"]
    resources = [aws_s3_bucket.data.arn, "${aws_s3_bucket.data.arn}/*"]
    principals {
      type        = "*"
      identifiers = ["*"]
    }
    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
  statement {
    sid       = "DenyOldTLS"
    effect    = "Deny"
    actions   = ["s3:*"]
    resources = [aws_s3_bucket.data.arn, "${aws_s3_bucket.data.arn}/*"]
    principals {
      type        = "*"
      identifiers = ["*"]
    }
    condition {
      test     = "NumericLessThan"
      variable = "s3:TlsVersion"
      values   = ["1.2"]
    }
  }
  # "IfExists": las subidas SIN header se cifran con el KMS por defecto;
  # solo se bloquean las que piden explicitamente otro algoritmo (p. ej. AES256).
  statement {
    sid       = "DenyExplicitNonKmsEncryption"
    effect    = "Deny"
    actions   = ["s3:PutObject"]
    resources = ["${aws_s3_bucket.data.arn}/*"]
    principals {
      type        = "*"
      identifiers = ["*"]
    }
    condition {
      test     = "StringNotEqualsIfExists"
      variable = "s3:x-amz-server-side-encryption"
      values   = ["aws:kms"]
    }
  }
}

resource "aws_s3_bucket_policy" "data" {
  bucket     = aws_s3_bucket.data.id
  policy     = data.aws_iam_policy_document.data.json
  depends_on = [aws_s3_bucket_public_access_block.data]
}
