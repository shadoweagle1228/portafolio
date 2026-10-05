terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.60" }
  }
}

variable "target_ids" {
  type        = list(string)
  description = "IDs de OUs o cuentas a las que se adjuntan las SCP"
}

variable "allowed_regions" {
  type    = list(string)
  default = ["us-east-1", "us-east-2"]
}

variable "budget_email" {
  type = string
}

variable "monthly_budget_usd" {
  type    = number
  default = 500
}

# ---------- SCPs (guardrails preventivos) ----------
data "aws_iam_policy_document" "guardrails" {
  statement {
    sid       = "DenyDisablePublicAccessBlock"
    effect    = "Deny"
    actions   = ["s3:PutAccountPublicAccessBlock", "s3:PutBucketPublicAccessBlock", "s3:PutBucketAcl", "s3:PutObjectAcl"]
    resources = ["*"]
  }
  statement {
    sid         = "DenyOutsideAllowedRegions"
    effect      = "Deny"
    not_actions = ["iam:*", "organizations:*", "route53:*", "cloudfront:*", "support:*", "sts:*", "budgets:*"]
    resources   = ["*"]
    condition {
      test     = "StringNotEquals"
      variable = "aws:RequestedRegion"
      values   = var.allowed_regions
    }
  }
  statement {
    sid       = "DenyRootUser"
    effect    = "Deny"
    actions   = ["*"]
    resources = ["*"]
    condition {
      test     = "StringLike"
      variable = "aws:PrincipalArn"
      values   = ["arn:aws:iam::*:root"]
    }
  }
  statement {
    sid       = "ProtectSecurityServices"
    effect    = "Deny"
    actions = [
      "cloudtrail:StopLogging", "cloudtrail:DeleteTrail",
      "guardduty:DeleteDetector", "guardduty:DisassociateFromMasterAccount",
      "config:StopConfigurationRecorder", "config:DeleteConfigurationRecorder",
    ]
    resources = ["*"]
  }
}

resource "aws_organizations_policy" "guardrails" {
  name    = "baseline-guardrails"
  type    = "SERVICE_CONTROL_POLICY"
  content = data.aws_iam_policy_document.guardrails.json
}

resource "aws_organizations_policy_attachment" "guardrails" {
  for_each  = toset(var.target_ids)
  policy_id = aws_organizations_policy.guardrails.id
  target_id = each.value
}

# ---------- Tag policy (estandar de etiquetado) ----------
resource "aws_organizations_policy" "tags" {
  name = "mandatory-tags"
  type = "TAG_POLICY"
  content = jsonencode({
    tags = {
      Environment = {
        tag_key          = { "@@assign" = "Environment" }
        tag_value        = { "@@assign" = ["dev", "qa", "prod"] }
        enforced_for     = { "@@assign" = ["s3:bucket"] }
      }
      Owner = { tag_key = { "@@assign" = "Owner" } }
      DataClassification = {
        tag_key   = { "@@assign" = "DataClassification" }
        tag_value = { "@@assign" = ["public", "internal", "confidential", "cardholder-data"] }
      }
    }
  })
}

resource "aws_organizations_policy_attachment" "tags" {
  for_each  = toset(var.target_ids)
  policy_id = aws_organizations_policy.tags.id
  target_id = each.value
}

# ---------- Control de costos ----------
resource "aws_budgets_budget" "monthly" {
  name         = "monthly-cost"
  budget_type  = "COST"
  limit_amount = tostring(var.monthly_budget_usd)
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.budget_email]
  }
  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = [var.budget_email]
  }
}

# ---------- Cumplimiento continuo: reglas de AWS Config para S3 ----------
resource "aws_config_config_rule" "s3_public_read_prohibited" {
  name = "s3-bucket-public-read-prohibited"
  source {
    owner             = "AWS"
    source_identifier = "S3_BUCKET_PUBLIC_READ_PROHIBITED"
  }
}

resource "aws_config_config_rule" "s3_ssl_only" {
  name = "s3-bucket-ssl-requests-only"
  source {
    owner             = "AWS"
    source_identifier = "S3_BUCKET_SSL_REQUESTS_ONLY"
  }
}

resource "aws_config_config_rule" "kms_rotation" {
  name = "cmk-backing-key-rotation-enabled"
  source {
    owner             = "AWS"
    source_identifier = "CMK_BACKING_KEY_ROTATION_ENABLED"
  }
}
