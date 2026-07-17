"""Tests for CLI parser and command routing."""

import io
import sys
from contextlib import redirect_stderr

from n8n_cli.cli import build_parser, _mask_key


class TestParserValidation:
    def test_active_inactive_mutually_exclusive(self):
        parser = build_parser()
        try:
            with redirect_stderr(io.StringIO()):
                parser.parse_args(["workflows", "list", "--active", "--inactive"])
            assert False, "Should reject --active --inactive together"
        except SystemExit as e:
            assert e.code == 2

    def test_method_choices_validation(self):
        parser = build_parser()
        try:
            with redirect_stderr(io.StringIO()):
                parser.parse_args(["webhooks", "test", "wf123", "--method", "BOGUS"])
            assert False, "Should reject invalid method"
        except SystemExit as e:
            assert e.code == 2

    def test_api_command_exists(self):
        parser = build_parser()
        args = parser.parse_args(["api", "/workflows"])
        assert hasattr(args, "func")
        assert args.path == "/workflows"
        assert args.method == "GET"

    def test_validate_command_exists(self):
        parser = build_parser()
        args = parser.parse_args(["workflows", "validate", "/tmp/test.json"])
        assert hasattr(args, "func")
        assert args.file == "/tmp/test.json"


class TestMaskKey:
    def test_empty_key(self):
        assert _mask_key("") == "(not set)"

    def test_short_key(self):
        assert _mask_key("abc") == "****"
        assert _mask_key("abcd") == "****"

    def test_long_key(self):
        # Dummy test value, not a real key
        test_val = "a" * 8 + "wxyz"
        result = _mask_key(test_val)
        assert result.startswith("****")
        assert result.endswith("wxyz")
        assert test_val not in result

    def test_key_not_leaked(self):
        test_val = "x" * 16
        masked = _mask_key(test_val)
        assert test_val not in masked
