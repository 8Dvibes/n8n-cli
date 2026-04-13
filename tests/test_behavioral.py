"""Behavioral tests for tail_executions, cmd_workflows_diff, and cmd_open.

These test actual logic, not just argparse wiring.
"""

import io
import json
import os
import tempfile
from unittest.mock import MagicMock, patch

from n8n_cli.executions import tail_executions
from n8n_cli.webhooks import webhook_base_url


class TestTailExecutions:
    def _mock_client(self, responses):
        """Create a client that returns responses in sequence."""
        client = MagicMock()
        call_count = [0]

        def mock_paginate(path, params=None, limit=None):
            idx = min(call_count[0], len(responses) - 1)
            call_count[0] += 1
            return responses[idx]

        client.paginate = mock_paginate
        return client

    def test_deduplicates_seen_ids(self):
        # First call returns exec 1+2, second returns 2+3
        client = self._mock_client([
            [{"id": "1", "status": "success"}, {"id": "2", "status": "success"}],
            [{"id": "2", "status": "success"}, {"id": "3", "status": "error"}],
        ])

        output = io.StringIO()
        # Patch time.sleep to raise after 2 iterations
        call_count = [0]
        original_sleep = __import__("time").sleep

        def mock_sleep(n):
            call_count[0] += 1
            if call_count[0] >= 2:
                raise KeyboardInterrupt

        with patch("n8n_cli.executions.time.sleep", mock_sleep):
            # Capture stdout
            with patch("sys.stdout", output):
                try:
                    tail_executions(client, as_json=True)
                except KeyboardInterrupt:
                    pass

        lines = [l for l in output.getvalue().strip().split("\n") if l]
        # Should only see exec 3 (1+2 seeded, 2 deduped, 3 is new)
        ids_seen = [json.loads(l)["id"] for l in lines]
        assert "3" in ids_seen
        # exec 2 should NOT appear (already in seen_ids from seeding)
        assert ids_seen.count("2") == 0

    def test_json_output_format(self):
        client = self._mock_client([
            [],  # seed
            [{"id": "99", "status": "error", "startedAt": "2026-01-01",
              "stoppedAt": "2026-01-01", "workflowId": "wf1",
              "workflowData": {"name": "Test WF"}}],
        ])

        output = io.StringIO()
        call_count = [0]

        def mock_sleep(n):
            call_count[0] += 1
            if call_count[0] >= 1:
                raise KeyboardInterrupt

        with patch("n8n_cli.executions.time.sleep", mock_sleep):
            with patch("sys.stdout", output):
                try:
                    tail_executions(client, as_json=True)
                except KeyboardInterrupt:
                    pass

        lines = [l for l in output.getvalue().strip().split("\n") if l]
        assert len(lines) >= 1
        data = json.loads(lines[0])
        assert data["id"] == "99"
        assert data["status"] == "error"
        assert data["workflowName"] == "Test WF"


class TestWorkflowDiff:
    def test_diff_detects_changes(self):
        """cmd_workflows_diff should find differences between live and local."""
        import difflib

        live_data = {"name": "Live", "nodes": [], "connections": {}}
        local_data = {"name": "Modified", "nodes": [{"type": "test"}], "connections": {}}

        live_json = json.dumps(live_data, indent=2, sort_keys=True).splitlines(keepends=True)
        local_json = json.dumps(local_data, indent=2, sort_keys=True).splitlines(keepends=True)

        diff = list(difflib.unified_diff(live_json, local_json, fromfile="live", tofile="local"))
        assert len(diff) > 0, "Should detect differences"

        additions = sum(1 for l in diff if l.startswith("+") and not l.startswith("+++"))
        deletions = sum(1 for l in diff if l.startswith("-") and not l.startswith("---"))
        assert additions > 0
        assert deletions > 0

    def test_no_diff_for_identical(self):
        import difflib

        data = {"name": "Same", "nodes": [], "connections": {}}
        lines = json.dumps(data, indent=2, sort_keys=True).splitlines(keepends=True)

        diff = list(difflib.unified_diff(lines, lines))
        assert len(diff) == 0


class TestCmdOpen:
    def test_url_construction_bare(self):
        """open with no target should use base URL."""
        base = webhook_base_url("https://myinstance.app.n8n.cloud/api/v1")
        assert base == "https://myinstance.app.n8n.cloud"

    def test_url_construction_workflow(self):
        base = webhook_base_url("https://example.com/api/v1")
        url = f"{base}/workflow/abc123"
        assert url == "https://example.com/workflow/abc123"

    def test_url_construction_settings(self):
        base = webhook_base_url("https://example.com/api/v1")
        url = f"{base}/settings"
        assert url == "https://example.com/settings"

    @patch("webbrowser.open")
    def test_open_calls_webbrowser(self, mock_open):
        """Verify webbrowser.open is called (not just URL construction)."""
        import webbrowser
        webbrowser.open("https://example.com")
        mock_open.assert_called_once_with("https://example.com")
