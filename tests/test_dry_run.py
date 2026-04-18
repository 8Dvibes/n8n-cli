"""Tests for --dry-run flag on mutation commands."""

import io
from contextlib import redirect_stderr

from n8n_cli.cli import build_parser


class TestDryRunParser:
    def test_delete_accepts_dry_run(self):
        parser = build_parser()
        args = parser.parse_args(["workflows", "delete", "wf123", "--dry-run"])
        assert args.dry_run is True
        assert args.id == "wf123"

    def test_activate_accepts_dry_run(self):
        parser = build_parser()
        args = parser.parse_args(["workflows", "activate", "wf123", "--dry-run"])
        assert args.dry_run is True

    def test_deactivate_accepts_dry_run(self):
        parser = build_parser()
        args = parser.parse_args(["workflows", "deactivate", "wf123", "--dry-run"])
        assert args.dry_run is True

    def test_dry_run_defaults_false(self):
        parser = build_parser()
        args = parser.parse_args(["workflows", "delete", "wf123"])
        assert args.dry_run is False
