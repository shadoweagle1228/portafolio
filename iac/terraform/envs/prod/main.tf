terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.60" }
  }
}

provider "aws" {
  region = "us-east-1"
  default_tags {
    tags = { ManagedBy = "terraform", Project = "portafolio", Compliance = "pci-dss-v4" }
  }
}

module "secure_bucket" {
  source             = "../../modules/secure-s3-bucket"
  bucket_name        = "edwin-portafolio-prod-cde-data"
  environment        = "prod"
  owner              = "platform-team"
  log_retention_days = 365
}
