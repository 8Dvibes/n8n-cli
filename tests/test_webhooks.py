"""Tests for webhook operations."""

from n8n_cli.webhooks import _webhook_base_url


class TestWebhookBaseUrl:
    def test_standard_api_v1(self):
        assert _webhook_base_url("https://example.com/api/v1") == "https://example.com"

    def test_trailing_slash(self):
        assert _webhook_base_url("https://example.com/api/v1/") == "https://example.com"

    def test_nonstandard_api_path(self):
        url = "https://example.com/api/v2"
        result = _webhook_base_url(url)
        # Should find /api/ and strip from there
        assert result == "https://example.com"

    def test_no_api_in_path(self):
        url = "https://example.com/custom/path"
        result = _webhook_base_url(url)
        # No /api/ found, returns as-is
        assert result == url

    def test_cloud_url(self):
        url = "https://myinstance.app.n8n.cloud/api/v1"
        assert _webhook_base_url(url) == "https://myinstance.app.n8n.cloud"


class TestWebhookMethodFix:
    """Regression test for the http_method NameError fix (PR #1)."""

    def test_no_undefined_http_method(self):
        import inspect
        from n8n_cli.webhooks import test_webhook
        source = inspect.getsource(test_webhook)
        # The old bug: print(f"Method: {http_method}") where http_method was undefined
        # The variable is called 'method', not 'http_method'
        lines = source.split("\n")
        for line in lines:
            if "http_method" in line and "http_method =" not in line:
                if not line.strip().startswith("#"):
                    assert False, f"Found undefined http_method reference: {line}"
