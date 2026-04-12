# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `n8n-cli api` command for raw REST API escape hatch
- `n8n-cli wf validate` command for pre-import workflow JSON validation
- Exception hierarchy (`N8nError` base with typed subclasses)
- Recovery hints in structured error responses
- 55 unit tests with pytest
- GitHub Actions CI for Python 3.9-3.13
- CHANGELOG.md and CONTRIBUTING.md

### Fixed
- NameError crash in `webhooks test` (`http_method` was undefined)
- `variables update` silently accepted empty updates (no `--key` or `--value`)
- `variables update --key ""` dropped empty string keys (truthiness bug)
- Empty node catalog could be persisted on partial download failure
- 13 skills updated to use `--json` for agent-parseable output

### Changed
- Domain modules raise exceptions instead of calling `sys.exit()`
- `N8nApiError` moved into unified exception hierarchy
- Error output includes `recovery_hint` for agent self-correction
- `cmd_health` uses central error handler instead of local try/except

### Removed
- Dead `resp` variable in `cmd_health()`
- Dead `import sys` in `workflows.py`
- Duplicated webhook URL derivation code (extracted to `_webhook_base_url()`)

## [0.4.1] - 2026-04-03

### Added
- `skills doctor` command to validate SKILL.md files against CLI surface
- `wf clear-tags` subcommand to remove all tags from a workflow

## [0.4.0] - 2026-04-02

### Added
- 33rd skill: `n8n-cli-from-launchd`
- Workflow JSON sanitizer fix for round-trip imports

## [0.3.0] - 2026-04-01

### Added
- 21 new skills bringing total to 32
- Skills organized into 7 categories

## [0.2.0] - 2026-03-30

### Added
- 11 bundled Claude Code skills with installer subcommand
- `skills install`, `skills list`, `skills uninstall`, `skills path`

## [0.1.0] - 2026-03-28

### Added
- Initial release on PyPI as `n8n-toolkit`
- 80+ commands across 13 command groups
- Zero external dependencies (stdlib only)
- Multi-profile configuration support
- Auto-updating node catalog from npm
- JSON output mode (`--json`) on all commands
- Cursor-based pagination for list endpoints
