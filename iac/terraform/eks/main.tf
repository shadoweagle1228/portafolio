terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.60" }
  }
}

provider "aws" {
  region = var.region
}

variable "region" {
  type    = string
  default = "us-east-1"
}

variable "cluster_name" {
  type    = string
  default = "portafolio-eks"
}

variable "vpc_id" {
  type = string
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "admin_role_arn" {
  type        = string
  description = "Rol IAM (SSO) con acceso admin al cluster"
}

data "aws_caller_identity" "current" {}
data "aws_partition" "current" {}

data "aws_iam_policy_document" "eks_kms" {
  statement {
    sid       = "KeyAdmin"
    actions   = ["kms:*"]
    resources = ["*"]
    principals {
      type        = "AWS"
      identifiers = ["arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.current.account_id}:root"]
    }
  }
}

# CMK para cifrar secretos de Kubernetes en etcd (envelope encryption)
resource "aws_kms_key" "eks" {
  description         = "Cifrado de secretos de ${var.cluster_name}"
  enable_key_rotation = true
  policy              = data.aws_iam_policy_document.eks_kms.json
}

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.24"

  cluster_name    = var.cluster_name
  cluster_version = "1.31"

  vpc_id     = var.vpc_id
  subnet_ids = var.private_subnet_ids

  # Security first: API privada, sin endpoint publico
  cluster_endpoint_public_access  = false
  cluster_endpoint_private_access = true

  cluster_encryption_config = {
    provider_key_arn = aws_kms_key.eks.arn
    resources        = ["secrets"]
  }

  # Auditoria del control plane (PCI DSS Req. 10)
  cluster_enabled_log_types              = ["api", "audit", "authenticator", "controllerManager", "scheduler"]
  cloudwatch_log_group_retention_in_days = 365

  enable_cluster_creator_admin_permissions = false
  authentication_mode                      = "API"
  access_entries = {
    admin = {
      principal_arn = var.admin_role_arn
      policy_associations = {
        admin = {
          policy_arn   = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy"
          access_scope = { type = "cluster" }
        }
      }
    }
  }

  eks_managed_node_groups = {
    default = {
      instance_types = ["m6i.large"]
      min_size       = 2
      desired_size   = 2
      max_size       = 6
      # IMDSv2 obligatorio
      metadata_options = {
        http_endpoint               = "enabled"
        http_tokens                 = "required"
        http_put_response_hop_limit = 1
      }
      ebs_optimized = true
      block_device_mappings = {
        xvda = {
          device_name = "/dev/xvda"
          ebs         = { volume_size = 50, volume_type = "gp3", encrypted = true }
        }
      }
    }
  }
}

output "cluster_name" {
  value = module.eks.cluster_name
}
