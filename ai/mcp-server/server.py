"""Servidor MCP (Model Context Protocol) de solo lectura para auditoria de buckets S3.

Permite a agentes de IA (Kiro, Claude Desktop, Antigravity) consultar el estado de
cumplimiento PCI DSS v4 de buckets en AWS de manera segura, estructurada y sin privilegios de escritura.
"""
from __future__ import annotations

import json
import sys
from dataclasses import asdict
from typing import Any

from auditor.adapters.s3_inspector import Boto3BucketInspector
from auditor.application.use_cases import AuditAllBuckets, AuditBucket

TOOLS_DEFINITION = [
    {
        "name": "audit_single_bucket",
        "description": "Audita un bucket de Amazon S3 contra los requisitos de seguridad de PCI DSS v4.0.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "bucket_name": {
                    "type": "string",
                    "description": "Nombre del bucket S3 a auditar (e.g. edwin-portafolio-dev-cde-data)"
                }
            },
            "required": ["bucket_name"]
        }
    },
    {
        "name": "audit_all_buckets",
        "description": "Audita todos los buckets S3 visibles en la cuenta AWS contra PCI DSS v4.0.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    }
]


class McpServer:
    def __init__(self, inspector: Any | None = None) -> None:
        self._inspector = inspector or Boto3BucketInspector()
        self._audit_bucket = AuditBucket(self._inspector)
        self._audit_all = AuditAllBuckets(self._inspector)

    def handle_request(self, request: dict[str, Any]) -> dict[str, Any]:
        req_id = request.get("id")
        method = request.get("method")

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": {"name": "pci-bucket-auditor-mcp", "version": "1.0.0"},
                    "capabilities": {"tools": {}}
                }
            }

        if method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": TOOLS_DEFINITION}
            }

        if method == "tools/call":
            params = request.get("params", {})
            tool_name = params.get("name")
            args = params.get("arguments", {})

            try:
                if tool_name == "audit_single_bucket":
                    bucket = args.get("bucket_name")
                    if not bucket:
                        raise ValueError("Falta el parametro 'bucket_name'")
                    report = self._audit_bucket(bucket)
                    data = asdict(report) | {"compliant": report.compliant}
                elif tool_name == "audit_all_buckets":
                    reports = self._audit_all()
                    data = [asdict(r) | {"compliant": r.compliant} for r in reports]
                else:
                    return {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {"code": -32601, "message": f"Herramienta no encontrada: {tool_name}"}
                    }

                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [
                            {"type": "text", "text": json.dumps(data, indent=2)}
                        ]
                    }
                }
            except Exception as e:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": f"Error ejecutando auditoria: {str(e)}"}],
                        "isError": True
                    }
                }

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Metodo no implementado: {method}"}
        }

    def run_stdio(self) -> None:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                req = json.loads(line)
                resp = self.handle_request(req)
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()
            except Exception as e:
                err_resp = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": str(e)}}
                sys.stdout.write(json.dumps(err_resp) + "\n")
                sys.stdout.flush()


if __name__ == "__main__":
    McpServer().run_stdio()
