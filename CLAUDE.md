# n8n-cli -- Project Context for AI Agents

This is a Python CLI tool that wraps the n8n REST API. Zero external dependencies (stdlib only).

## What this tool does

n8n-cli gives you full control of n8n workflow automation instances from the terminal. It replaces clicking through the n8n web UI or running heavy MCP servers.

**Use cases:**
- List, create, update, activate, deactivate, export, import workflows
- View and debug execution history (filter by status, workflow, etc.)
- Manage credentials, tags, variables, projects, users
- Search and browse 543+ n8n nodes with full property schemas
- Test webhook endpoints from the command line
- Run security audits
- Switch between multiple n8n instances (cloud + self-hosted)

## Architecture

```
n8n_cli/
  cli.py          -- argparse CLI entrypoint, all subcommand routing
  client.py       -- urllib-based REST client (GET/POST/PUT/PATCH/DELETE + pagination)
  config.py       -- Multi-profile config (~/.n8n-cli.json) with env var overrides
  skills.py       -- Bundled Claude Code skills installer (list/install/uninstall/path)
  skills_data/    -- 11 SKILL.md files shipped as package data
  workflows.py    -- Workflow CRUD + export/import/activate/archive/transfer
  executions.py   -- Execution history, retry, stop, error analysis
  credentials.py  -- Credential listing + schema lookup
  nodes.py        -- Auto-updating node catalog from npm (543+ nodes)
  webhooks.py     -- Webhook URL discovery + test payloads
  tags.py         -- Tag CRUD
  variables.py    -- Variable CRUD
  projects.py     -- Project management
  users.py        -- User management
  audit.py        -- Security audit reports
  source_control.py    -- Source control pull
  community_packages.py -- Community package management
```

## Claude Code skills

`n8n_cli/skills_data/` is the canonical home for the 11 Claude Code skills that ship with the tool. Each subdirectory is a skill (e.g. `n8n-cli-status/SKILL.md`). The `skills.py` module reads them via `importlib.resources.files("n8n_cli.skills_data")` so it works from editable installs, wheels, and sdists alike.

`pyproject.toml` declares `[tool.setuptools.package-data]` to include `**/*.md` (and any future helper files) inside the wheel. **Do not move the skills out of the package** -- moving them to a repo-root `skills/` directory would break PyPI installs.

To add a new skill: drop a new directory under `n8n_cli/skills_data/<skill-name>/` with a `SKILL.md` containing YAML frontmatter (`name`, `description`, `user_invocable: true`). Bump the README skill table and the version in both `pyproject.toml` and `n8n_cli/__init__.py`.

## Key design decisions

- **Zero dependencies**: Only Python stdlib. No requests, no click, no rich. This keeps it installable everywhere without conflicts.
- **Multi-profile**: Config supports named profiles for different n8n instances. Env vars override config.
- **Auto-updating node catalog**: Downloads node definitions from official n8n npm packages. Checks for new versions on every use (single HTTP call to npm registry). No stale data.
- **JSON output**: Every command supports `--json` for machine-readable output and piping.
- **Cursor-based pagination**: Handles n8n's pagination automatically (max 250 per page, cursor-based).

## Auth

n8n uses API keys passed as `X-N8N-API-KEY` header. Keys are stored in `~/.n8n-cli.json` (mode 600) or via `N8N_API_URL` and `N8N_API_KEY` environment variables.

## Testing

```bash
n8n-cli health                              # Check connection
n8n-cli workflows list --active             # List active workflows
n8n-cli nodes search slack                  # Search node catalog
n8n-cli --json executions list --status error --limit 5   # Recent failures as JSON
```

## n8n API reference

- Base URL pattern: `https://<instance>.app.n8n.cloud/api/v1` (cloud) or `https://<host>/api/v1` (self-hosted)
- Auth: `X-N8N-API-KEY` header
- Pagination: cursor-based with `nextCursor` response field and `cursor` query param
- Rate limits: varies by plan
- OpenAPI spec: `packages/cli/src/public-api/v1/openapi.yml` in n8n source
