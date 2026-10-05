terraform {
  required_version = ">= 1.6.0"

  # Estado remoto cifrado y con lock (descomentar al usar en una cuenta real)
  # backend "s3" {
  #   bucket         = "<tfstate-bucket>"
  #   key            = "secure-s3/dev/terraform.tfstate"
  #   region         = "us-east-1"
  #   encrypt        = true
  #   kms_key_id     = "alias/tfstate"
  #   dynamodb_table = "tfstate-lock"
  # }
}

provider "aws" {
  region = "us-east-1"
  default_tags {
    tags = { ManagedBy = "terraform", Project = "portafolio" }
  }
}

module "secure_bucket" {
  source              = "../../modules/secure-s3-bucket"
  bucket_name         = "edwin-portafolio-dev-cde-data"
  environment         = "dev"
  owner               = "platform-team"
  key_admin_role_arns = var.key_admin_role_arns
  key_user_role_arns  = var.key_user_role_arns
  log_retention_days  = 365
}

output "bucket_arn" {
  value = module.secure_bucket.bucket_arn
}

variable "key_admin_role_arns" {
  type        = list(string)
  description = "Roles que administran la llave KMS; incluir el rol de despliegue"
}

variable "key_user_role_arns" {
  type        = list(string)
  description = "Roles de aplicacion que usan la llave via S3"
}
