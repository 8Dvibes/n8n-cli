"""Tests for community package operations."""

from n8n_cli.community_packages import _encode_pkg


class TestEncodePkg:
    def test_scoped_package(self):
        assert _encode_pkg("@scope/pkg") == "%40scope%2Fpkg"

    def test_unscoped_package(self):
        assert _encode_pkg("simple-pkg") == "simple-pkg"

    def test_n8n_langchain_package(self):
        assert _encode_pkg("@n8n/n8n-nodes-langchain") == "%40n8n%2Fn8n-nodes-langchain"
