import io
import json
import unittest
import urllib.error
from contextlib import redirect_stdout
from unittest.mock import MagicMock, patch

from n8n_cli import webhooks


class FakeClient:
    """Stands in for N8nClient so no live n8n instance is contacted."""

    api_url = "https://n8n.example/api/v1"

    def __init__(self, http_method=None):
        params = {"path": "camp-intake"}
        if http_method is not None:
            params["httpMethod"] = http_method
        self.workflow = {
            "name": "Camp Intake",
            "nodes": [
                {
                    "name": "Intake Webhook",
                    "type": "n8n-nodes-base.webhook",
                    "parameters": params,
                }
            ],
        }

    def get(self, path):
        assert path == "/workflows/wf123"
        return self.workflow


def fake_response(body, status=200):
    resp = MagicMock()
    resp.read.return_value = body.encode("utf-8")
    resp.status = status
    resp.__enter__.return_value = resp
    return resp


class TestWebhookHumanOutput(unittest.TestCase):
    """Regression: `wh test` without --json raised NameError on http_method."""

    def run_test_webhook(self, client, **kwargs):
        out = io.StringIO()
        with patch("urllib.request.urlopen") as urlopen, redirect_stdout(out):
            urlopen.return_value = fake_response(json.dumps({"ok": True}))
            webhooks.test_webhook(client, "wf123", as_json=False, **kwargs)
        return out.getvalue(), urlopen

    def test_prints_node_configured_method(self):
        output, urlopen = self.run_test_webhook(FakeClient(http_method="GET"))

        self.assertIn("Method:    GET", output)
        self.assertIn("URL:       https://n8n.example/webhook-test/camp-intake", output)
        self.assertIn("Status: 200", output)
        self.assertIn('"ok": true', output)
        sent = urlopen.call_args[0][0]
        self.assertEqual(sent.get_method(), "GET")
        self.assertEqual(sent.full_url, "https://n8n.example/webhook-test/camp-intake")

    def test_defaults_to_post_with_payload(self):
        output, urlopen = self.run_test_webhook(FakeClient(), data='{"name": "Ada"}')

        self.assertIn("Method:    POST", output)
        sent = urlopen.call_args[0][0]
        self.assertEqual(sent.get_method(), "POST")
        self.assertEqual(json.loads(sent.data), {"name": "Ada"})

    def test_http_error_prints_status_and_exits(self):
        out = io.StringIO()
        err = urllib.error.HTTPError(
            "https://n8n.example/webhook-test/camp-intake", 404, "Not Found", {},
            io.BytesIO(b"webhook not registered"),
        )
        self.addCleanup(err.close)
        with patch("urllib.request.urlopen", side_effect=err), redirect_stdout(out):
            with self.assertRaises(SystemExit) as exit_info:
                webhooks.test_webhook(FakeClient(), "wf123", as_json=False)

        self.assertEqual(exit_info.exception.code, 1)
        self.assertIn("Method:    POST", out.getvalue())
        self.assertIn("Status: 404", out.getvalue())
        self.assertIn("Error: webhook not registered", out.getvalue())


if __name__ == "__main__":
    unittest.main()
