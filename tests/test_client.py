"""Tests for the HTTP client."""

import json
import urllib.error
from unittest.mock import MagicMock, patch

from n8n_cli.client import N8nClient
from n8n_cli.exceptions import N8nApiError, N8nConnectionError


class TestN8nClient:
    def _client(self):
        return N8nClient("https://example.com/api/v1", "fake-test-value")

    @patch("n8n_cli.client.urllib.request.urlopen")
    def test_get_builds_correct_url(self, mock_urlopen):
        resp = MagicMock()
        resp.status = 200
        resp.read.return_value = b'{"data": []}'
        resp.__enter__ = lambda s: s
        resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = resp

        client = self._client()
        result = client.get("/workflows", params={"limit": 1})

        call_args = mock_urlopen.call_args
        req = call_args[0][0]
        assert "example.com/api/v1/workflows" in req.full_url
        assert "limit=1" in req.full_url
        assert req.get_header("X-n8n-api-key") == "fake-test-value"

    @patch("n8n_cli.client.urllib.request.urlopen")
    def test_http_error_raises_api_error(self, mock_urlopen):
        error = urllib.error.HTTPError(
            "https://example.com", 404, "Not Found", {},
            MagicMock(read=lambda: b'{"message": "not found"}'),
        )
        mock_urlopen.side_effect = error

        client = self._client()
        try:
            client.get("/workflows/bad-id")
            assert False, "Should have raised"
        except N8nApiError as e:
            assert e.status == 404
            assert "not found" in e.message.lower()

    @patch("n8n_cli.client.urllib.request.urlopen")
    def test_url_error_raises_connection_error(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")

        client = self._client()
        try:
            client.get("/workflows")
            assert False, "Should have raised"
        except N8nConnectionError as e:
            assert "Connection refused" in str(e)

    @patch("n8n_cli.client.urllib.request.urlopen")
    def test_paginate_single_page(self, mock_urlopen):
        resp = MagicMock()
        resp.status = 200
        resp.read.return_value = json.dumps({
            "data": [{"id": "1"}, {"id": "2"}],
        }).encode()
        resp.__enter__ = lambda s: s
        resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = resp

        client = self._client()
        items = client.paginate("/workflows")
        assert len(items) == 2

    @patch("n8n_cli.client.urllib.request.urlopen")
    def test_paginate_with_limit(self, mock_urlopen):
        resp = MagicMock()
        resp.status = 200
        resp.read.return_value = json.dumps({
            "data": [{"id": str(i)} for i in range(10)],
        }).encode()
        resp.__enter__ = lambda s: s
        resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = resp

        client = self._client()
        items = client.paginate("/workflows", limit=3)
        assert len(items) == 3
