#!/usr/bin/env bash
# SecCheck local: escaneos de seguridad sobre la IaC y la cuenta AWS.
# Requiere: checkov, cfn-lint, (opcional) prowler con credenciales de solo lectura.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "==> Checkov (IaC)"
checkov -d "$ROOT/iac" --config-file "$ROOT/security/checkov.yaml"

echo "==> cfn-lint"
cfn-lint "$ROOT"/iac/cloudformation/*.yaml

if command -v prowler >/dev/null 2>&1; then
  echo "==> Prowler: PCI DSS v4.0 en la cuenta actual"
  prowler aws --compliance pci_4.0_aws --services s3 kms cloudtrail --output-formats html json-ocsf
else
  echo "(prowler no instalado: omitiendo escaneo de cuenta)"
fi
