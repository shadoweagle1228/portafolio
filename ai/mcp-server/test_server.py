"""Pruebas unitarias del servidor MCP."""
import json
from server import McpServer


class FakeInspector:
    def list_buckets(self):
        return ["edwin-test-bucket"]

    def inspect(self, name):
        from auditor.domain.model import BucketConfiguration
        return BucketConfiguration(
            name=name,
            public_access_blocked=True,
            encryption_algorithm="aws:kms",
            kms_rotation_enabled=True,
            versioning_enabled=True,
            access_logging_enabled=True,
            tls_enforced=True
        )


def test_mcp_initialize():
    server = McpServer(FakeInspector())
    resp = server.handle_request({"id": 1, "method": "initialize"})
    assert resp["result"]["serverInfo"]["name"] == "pci-bucket-auditor-mcp"


def test_mcp_list_tools():
    server = McpServer(FakeInspector())
    resp = server.handle_request({"id": 2, "method": "tools/list"})
    tools = resp["result"]["tools"]
    assert any(t["name"] == "audit_single_bucket" for t in tools)
    assert any(t["name"] == "audit_all_buckets" for t in tools)


def test_mcp_call_audit_single_bucket():
    server = McpServer(FakeInspector())
    resp = server.handle_request({
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "audit_single_bucket",
            "arguments": {"bucket_name": "edwin-test-bucket"}
        }
    })
    content = resp["result"]["content"][0]["text"]
    data = json.loads(content)
    assert data["compliant"] is True
    assert data["bucket"] == "edwin-test-bucket"
