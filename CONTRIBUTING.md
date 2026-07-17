# Contributing to n8n-cli

Thank you for your interest in contributing to n8n-cli.

## Development Setup

```bash
# Clone the repo
git clone https://github.com/8Dvibes/n8n-cli.git
cd n8n-cli

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Verify the CLI works
n8n-cli --version
n8n-cli skills doctor
```

## Project Structure

```
n8n_cli/
  cli.py              # argparse CLI entrypoint, all subcommand routing
  client.py           # urllib-based REST client (zero deps)
  config.py           # Multi-profile config (~/.n8n-cli.json)
  exceptions.py       # Exception hierarchy (N8nError base)
  workflows.py        # Workflow CRUD + sanitizer + validation
  executions.py       # Execution history, retry, stop
  credentials.py      # Credential listing + schema lookup
  nodes.py            # Auto-updating node catalog from npm
  webhooks.py         # Webhook URL discovery + test payloads
  tags.py             # Tag CRUD
  variables.py        # Variable CRUD
  projects.py         # Project management
  users.py            # User management
  audit.py            # Security audit reports
  source_control.py   # Source control pull
  community_packages.py  # Community package management
  skills.py           # Claude Code skills installer + doctor
  skills_data/        # 33 bundled SKILL.md files
tests/                # pytest test suite (55 tests)
```

## Key Design Decisions

- **Zero external dependencies.** Only Python stdlib. No requests, no click, no rich.
- **Every command supports `--json`.** Machine-readable output for AI agents.
- **Domain modules raise exceptions, not `sys.exit()`.** Makes the code testable.
- **Workflow JSON sanitizer.** Handles n8n API quirks for clean round-trips.

## Adding a New Command

1. Add the function in the appropriate domain module (e.g., `workflows.py`)
2. Add a `cmd_*` wrapper in `cli.py` with lazy import
3. Add the argparse entry in `build_parser()`
4. Add tests in `tests/`
5. Run `n8n-cli skills doctor` to verify no skill references broke

## Adding a New Skill

1. Create `n8n_cli/skills_data/<skill-name>/SKILL.md`
2. Add YAML frontmatter: `name`, `description`, `user_invocable: true`
3. Write the procedure using `n8n-cli` commands
4. Use `--json` for commands that produce output agents need to parse
5. Run `n8n-cli skills doctor` to validate
6. Update README skill table and version

See `CLAUDE.md` for detailed skill design principles.

## Running Tests

```bash
# All tests
pytest tests/ -v

# Specific module
pytest tests/test_workflows.py -v

# With coverage (if coverage is installed)
pytest tests/ --cov=n8n_cli --cov-report=term-missing
```

## Pull Request Guidelines

- One logical change per PR
- Include tests for new functionality
- Run `n8n-cli skills doctor` before submitting (must pass 33/33)
- All existing tests must pass
- Follow existing code style (no external formatters required)
