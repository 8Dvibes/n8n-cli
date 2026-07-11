"""Tests for node catalog operations."""

from unittest.mock import patch

from n8n_cli.nodes import _build_catalog_entry


class TestBuildCatalogEntry:
    def _sample_node(self):
        return {
            "name": "n8n-nodes-base.slack",
            "displayName": "Slack",
            "description": "Consume Slack API",
            "group": ["output"],
            "version": 2,
            "usableAsTool": True,
            "credentials": [{"name": "slackApi"}],
            "properties": [
                {"name": "resource", "options": [{"name": "channel"}, {"name": "message"}]},
                {"name": "operation", "options": [{"name": "create"}, {"name": "getAll"}]},
            ],
            "codex": {
                "categories": ["Communication"],
                "alias": ["slack-bot"],
                "resources": {"primaryDocumentation": [{"url": "https://docs.n8n.io/nodes/slack"}]},
            },
            "inputs": ["main"],
            "outputs": ["main"],
        }

    def test_extracts_basic_fields(self):
        entry = _build_catalog_entry(self._sample_node())
        assert entry["name"] == "n8n-nodes-base.slack"
        assert entry["displayName"] == "Slack"
        assert entry["description"] == "Consume Slack API"

    def test_extracts_categories(self):
        entry = _build_catalog_entry(self._sample_node())
        assert entry["categories"] == ["Communication"]

    def test_extracts_credentials(self):
        entry = _build_catalog_entry(self._sample_node())
        assert entry["credentials"] == ["slackApi"]

    def test_extracts_operations_and_resources(self):
        entry = _build_catalog_entry(self._sample_node())
        assert "create" in entry["operations"]
        assert "getAll" in entry["operations"]
        assert "channel" in entry["resources"]
        assert "message" in entry["resources"]

    def test_extracts_aliases(self):
        entry = _build_catalog_entry(self._sample_node())
        assert entry["aliases"] == ["slack-bot"]

    def test_extracts_ai_tool_flag(self):
        entry = _build_catalog_entry(self._sample_node())
        assert entry["usableAsTool"] is True

    def test_handles_missing_codex(self):
        node = {"name": "simple", "displayName": "S", "description": ""}
        entry = _build_catalog_entry(node)
        assert entry["categories"] == []
        assert entry["aliases"] == []
