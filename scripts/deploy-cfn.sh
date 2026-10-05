#!/usr/bin/env bash
# Despliega el template CloudFormation de bucket seguro.
# Uso: ./scripts/deploy-cfn.sh <dev|qa|prod>
set -euo pipefail

ENVIRONMENT="${1:?Uso: $0 <dev|qa|prod>}"
case "$ENVIRONMENT" in dev|qa|prod) ;; *) echo "Ambiente invalido" >&2; exit 2;; esac

STACK="secure-storage-${ENVIRONMENT}"
TEMPLATE="$(dirname "$0")/../iac/cloudformation/secure-s3-bucket.yaml"

cfn-lint "$TEMPLATE"

aws cloudformation deploy \
  --stack-name "$STACK" \
  --template-file "$TEMPLATE" \
  --no-fail-on-empty-changeset \
  --parameter-overrides \
      BucketName="edwin-portafolio-${ENVIRONMENT}-cde-data" \
      Environment="$ENVIRONMENT" \
      Owner="platform-team" \
  --tags Project=portafolio Compliance=pci-dss-v4

aws cloudformation describe-stacks --stack-name "$STACK" --query "Stacks[0].Outputs" --output table
