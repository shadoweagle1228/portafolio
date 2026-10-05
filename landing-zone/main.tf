terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.60" }
  }
}

# Se ejecuta en la cuenta de management de la organizacion.
# Nota: con Control Tower, las OUs/cuentas se gestionan via Account Factory (AFT);
# este modulo muestra el modelo equivalente con Organizations puro.

variable "security_email" { type = string }
variable "workload_accounts" {
  type = map(object({ email = string, ou = string })) # ou: sandbox | nonprod | prod
  default = {}
}

data "aws_organizations_organization" "this" {}

locals {
  root_id = data.aws_organizations_organization.this.roots[0].id
  ous     = toset(["security", "infrastructure", "sandbox", "nonprod", "prod"])
}

resource "aws_organizations_organizational_unit" "ou" {
  for_each  = local.ous
  name      = each.value
  parent_id = local.root_id
}

resource "aws_organizations_account" "workload" {
  for_each                   = var.workload_accounts
  name                       = each.key
  email                      = each.value.email
  parent_id                  = aws_organizations_organizational_unit.ou[each.value.ou].id
  role_name                  = "OrganizationAccountAccessRole"
  close_on_deletion          = false
  iam_user_access_to_billing = "DENY"
  lifecycle { ignore_changes = [role_name] }
}

# Bucket de CloudTrail organizacional (inmutable, cifrado, 12 meses - PCI 10.5.1)
resource "aws_s3_bucket" "trail" {
  bucket              = "org-cloudtrail-${data.aws_organizations_organization.this.master_account_id}"
  object_lock_enabled = true
}

resource "aws_s3_bucket_public_access_block" "trail" {
  bucket                  = aws_s3_bucket.trail.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "trail" {
  bucket = aws_s3_bucket.trail.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "trail" {
  bucket = aws_s3_bucket.trail.id
  rule {
    apply_server_side_encryption_by_default { sse_algorithm = "AES256" }
  }
}

resource "aws_s3_bucket_object_lock_configuration" "trail" {
  bucket = aws_s3_bucket.trail.id
  rule {
    default_retention {
      mode = "COMPLIANCE"
      days = 365
    }
  }
  depends_on = [aws_s3_bucket_versioning.trail]
}

data "aws_iam_policy_document" "trail" {
  statement {
    sid       = "AclCheck"
    actions   = ["s3:GetBucketAcl"]
    resources = [aws_s3_bucket.trail.arn]
    principals {
      type        = "Service"
      identifiers = ["cloudtrail.amazonaws.com"]
    }
  }
  statement {
    sid       = "Write"
    actions   = ["s3:PutObject"]
    resources = ["${aws_s3_bucket.trail.arn}/AWSLogs/*"]
    principals {
      type        = "Service"
      identifiers = ["cloudtrail.amazonaws.com"]
    }
    condition {
      test     = "StringEquals"
      variable = "s3:x-amz-acl"
      values   = ["bucket-owner-full-control"]
    }
  }
  statement {
    sid       = "DenyInsecureTransport"
    effect    = "Deny"
    actions   = ["s3:*"]
    resources = [aws_s3_bucket.trail.arn, "${aws_s3_bucket.trail.arn}/*"]
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
}

resource "aws_s3_bucket_policy" "trail" {
  bucket = aws_s3_bucket.trail.id
  policy = data.aws_iam_policy_document.trail.json
}

resource "aws_cloudtrail" "org" {
  name                          = "org-trail"
  s3_bucket_name                = aws_s3_bucket.trail.id
  is_organization_trail         = true
  is_multi_region_trail         = true
  include_global_service_events = true
  enable_log_file_validation    = true
  depends_on                    = [aws_s3_bucket_policy.trail]
}

# GuardDuty con administrador delegado y auto-habilitacion
resource "aws_guardduty_detector" "main" {
  enable = true
  datasources {
    s3_logs { enable = true }
  }
}

resource "aws_guardduty_organization_configuration" "org" {
  detector_id                      = aws_guardduty_detector.main.id
  auto_enable_organization_members = "ALL"
}

output "ou_ids" {
  value = { for k, v in aws_organizations_organizational_unit.ou : k => v.id }
}
