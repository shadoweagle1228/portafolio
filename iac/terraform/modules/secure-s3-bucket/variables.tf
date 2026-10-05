terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.60"
    }
  }
}

variable "bucket_name" {
  type        = string
  description = "Nombre del bucket de datos"
  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9.-]{2,62}$", var.bucket_name))
    error_message = "Nombre de bucket invalido."
  }
}

variable "environment" {
  type = string
  validation {
    condition     = contains(["dev", "qa", "prod"], var.environment)
    error_message = "environment debe ser dev, qa o prod."
  }
}

variable "data_classification" {
  type    = string
  default = "cardholder-data"
}

variable "owner" {
  type = string
}

variable "log_retention_days" {
  type    = number
  default = 365
  validation {
    condition     = var.log_retention_days >= 365
    error_message = "PCI DSS 10.5.1 exige minimo 12 meses de retencion."
  }
}

variable "key_admin_role_arns" {
  type        = list(string)
  description = "Roles IAM que administran la llave KMS (sin acceso a datos). Debe incluir el rol que ejecuta terraform. Deben existir."
  validation {
    condition     = length(var.key_admin_role_arns) > 0
    error_message = "Se requiere al menos un administrador de la llave."
  }
}

variable "key_user_role_arns" {
  type        = list(string)
  description = "Roles IAM de aplicaciones que cifran/descifran datos (solo via S3)."
  validation {
    condition     = length(var.key_user_role_arns) > 0
    error_message = "Se requiere al menos un rol usuario de la llave."
  }
}

variable "tags" {
  type    = map(string)
  default = {}
}

output "bucket_arn" {
  value = aws_s3_bucket.data.arn
}

output "kms_key_arn" {
  value = aws_kms_key.data.arn
}

output "logs_bucket_name" {
  value = aws_s3_bucket.logs.id
}

output "cloudtrail_data_events_resource_arn" {
  description = "Agregar a los Advanced Event Selectors del trail (S3 data events, Req. 10.2)."
  value       = "${aws_s3_bucket.data.arn}/"
}
