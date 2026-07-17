"""Tests for shell completion generation."""

from n8n_cli.cli import build_parser
from n8n_cli.completions import generate_bash, generate_zsh


class TestBashCompletion:
    def test_generates_valid_script(self):
        parser = build_parser()
        script = generate_bash(parser)
        assert "complete -o default" in script
        assert "n8n-cli" in script
        assert "COMPREPLY" in script

    def test_includes_top_commands(self):
        parser = build_parser()
        script = generate_bash(parser)
        for cmd in ("workflows", "executions", "nodes", "skills", "api", "health"):
            assert cmd in script, f"Missing command: {cmd}"

    def test_includes_subcommands(self):
        parser = build_parser()
        script = generate_bash(parser)
        assert "list" in script
        assert "get" in script


class TestZshCompletion:
    def test_generates_valid_script(self):
        parser = build_parser()
        script = generate_zsh(parser)
        assert "#compdef n8n-cli" in script
        assert "_n8n_cli" in script

    def test_includes_top_commands(self):
        parser = build_parser()
        script = generate_zsh(parser)
        for cmd in ("workflows", "executions", "nodes", "skills"):
            assert cmd in script, f"Missing command: {cmd}"


class TestCompletionCommand:
    def test_command_exists(self):
        parser = build_parser()
        args = parser.parse_args(["completion", "bash"])
        assert hasattr(args, "func")
        assert args.shell == "bash"

    def test_zsh_option(self):
        parser = build_parser()
        args = parser.parse_args(["completion", "zsh"])
        assert args.shell == "zsh"
