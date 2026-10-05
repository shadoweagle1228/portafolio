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
