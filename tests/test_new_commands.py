"""Tests for exec tail, wf diff, and open commands."""

from n8n_cli.cli import build_parser


class TestExecTail:
    def test_command_exists(self):
        parser = build_parser()
        args = parser.parse_args(["executions", "tail"])
        assert hasattr(args, "func")
        assert args.interval == 3.0

    def test_with_filters(self):
        parser = build_parser()
        args = parser.parse_args([
            "exec", "tail",
            "--workflow-id", "wf123",
            "--status", "error",
            "--interval", "5",
        ])
        assert args.workflow_id == "wf123"
        assert args.status == "error"
        assert args.interval == 5.0

    def test_alias_works(self):
        parser = build_parser()
        args = parser.parse_args(["exec", "tail"])
        assert hasattr(args, "func")


class TestWorkflowDiff:
    def test_command_exists(self):
        parser = build_parser()
        args = parser.parse_args(["workflows", "diff", "wf123", "/tmp/local.json"])
        assert hasattr(args, "func")
        assert args.id == "wf123"
        assert args.file == "/tmp/local.json"

    def test_alias_works(self):
        parser = build_parser()
        args = parser.parse_args(["wf", "diff", "abc", "/tmp/x.json"])
        assert args.id == "abc"


class TestOpen:
    def test_bare_open(self):
        parser = build_parser()
        args = parser.parse_args(["open"])
        assert hasattr(args, "func")
        assert args.target is None

    def test_open_workflow(self):
        parser = build_parser()
        args = parser.parse_args(["open", "workflow", "abc123"])
        assert args.target == "workflow"
        assert args.target_id == "abc123"

    def test_open_settings(self):
        parser = build_parser()
        args = parser.parse_args(["open", "settings"])
        assert args.target == "settings"

    def test_open_credentials(self):
        parser = build_parser()
        args = parser.parse_args(["open", "credentials"])
        assert args.target == "credentials"
