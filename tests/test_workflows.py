"""Tests for workflow operations — sanitizer and validation."""

import json
import os
import tempfile

from n8n_cli.workflows import _sanitize_workflow_payload, validate_workflow


class TestSanitizeWorkflowPayload:
    def test_strips_readonly_fields(self):
        dirty = {
            "id": "123", "name": "Test", "nodes": [], "connections": {},
            "createdAt": "2024-01-01", "updatedAt": "2024-01-01",
            "versionId": "abc", "meta": {"instanceId": "x"},
            "pinData": {}, "staticData": None,
            "tags": [{"id": "1"}], "triggerCount": 5,
            "shared": [], "activeVersionId": "v1",
            "settings": {"executionOrder": "v1"},
        }
        clean = _sanitize_workflow_payload(dirty)
        for field in ("id", "createdAt", "updatedAt", "versionId",
                       "meta", "pinData", "staticData", "tags",
                       "triggerCount", "shared", "activeVersionId"):
            assert field not in clean, f"{field} not stripped"

    def test_preserves_allowed_fields(self):
        payload = {
            "name": "Keep", "nodes": [{"type": "test"}],
            "connections": {"a": "b"}, "settings": {"executionOrder": "v1"},
        }
        clean = _sanitize_workflow_payload(payload)
        assert clean["name"] == "Keep"
        assert clean["nodes"] == [{"type": "test"}]
        assert clean["connections"] == {"a": "b"}

    def test_strips_invalid_settings(self):
        payload = {
            "name": "T", "nodes": [], "connections": {},
            "settings": {
                "executionOrder": "v1",
                "callerPolicy": "any",
                "availableInMCP": True,
                "timeSavedMode": "auto",
            },
        }
        clean = _sanitize_workflow_payload(payload)
        assert "callerPolicy" not in clean["settings"]
        assert "availableInMCP" not in clean["settings"]
        assert "timeSavedMode" not in clean["settings"]
        assert clean["settings"]["executionOrder"] == "v1"

    def test_adds_default_execution_order(self):
        payload = {"name": "X", "nodes": [], "connections": {}}
        clean = _sanitize_workflow_payload(payload)
        assert clean["settings"]["executionOrder"] == "v1"

    def test_idempotent(self):
        payload = {
            "name": "I", "nodes": [], "connections": {},
            "settings": {"executionOrder": "v1"},
        }
        once = _sanitize_workflow_payload(payload)
        twice = _sanitize_workflow_payload(once)
        assert once == twice


class TestValidateWorkflow:
    def _validate_json(self, data):
        """Helper: write data to temp file, validate, return captured output."""
        fd, path = tempfile.mkstemp(suffix=".json")
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(data, f)
            # Capture JSON output
            import io
            import sys
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()
            try:
                validate_workflow(path, as_json=True)
            finally:
                output = sys.stdout.getvalue()
                sys.stdout = old_stdout
            return json.loads(output)
        finally:
            os.unlink(path)

    def test_valid_workflow(self):
        result = self._validate_json({
            "name": "Valid",
            "nodes": [{"type": "n8n-nodes-base.webhook", "name": "WH", "position": [0, 0]}],
            "connections": {},
            "settings": {"executionOrder": "v1"},
        })
        assert result["valid"] is True
        assert result["errors"] == []
        assert result["node_count"] == 1

    def test_missing_required_fields(self):
        result = self._validate_json({"nodes": [], "connections": {}})
        assert result["valid"] is False
        assert any("name" in e for e in result["errors"])

    def test_duplicate_node_names(self):
        result = self._validate_json({
            "name": "Dup",
            "nodes": [
                {"type": "a", "name": "Same", "position": [0, 0]},
                {"type": "b", "name": "Same", "position": [1, 1]},
            ],
            "connections": {},
        })
        assert result["valid"] is False
        assert any("duplicate" in e.lower() for e in result["errors"])

    def test_warns_about_stripped_settings(self):
        result = self._validate_json({
            "name": "W",
            "nodes": [],
            "connections": {},
            "settings": {"executionOrder": "v1", "callerPolicy": "any"},
        })
        assert result["valid"] is True
        assert any("callerPolicy" in w for w in result["warnings"])
