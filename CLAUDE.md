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

`n8n_cli/skills_data/` is the canonical home for the 40 Claude Code skills that ship with the tool, organized into 8 categories:

- **Core ops** (11): status, debug, create, import, export, monitor, migrate, backup, diff, webhook-test, creds
- **Hygiene** (4): cleanup, cost, schedule-audit, tag-governance
- **Authoring** (4): document, template, refactor, review
- **Dependency mapping** (3): deps, impact, node-usage
- **Production ops** (3): meta-monitor, upgrade-preflight, bulk
- **Testing** (3): test-fixtures, replay, smoke
- **Bridge to other tools** (5): from-mcp, to-mcp, from-cron, from-launchd, from-zapier
- **Expert reference** (7): code-javascript, code-python, expression-syntax, mcp-tools-expert, node-configuration, validation-expert, workflow-patterns

Each subdirectory is a skill (e.g. `n8n-cli-status/SKILL.md`). The `skills.py` module reads them via `importlib.resources.files("n8n_cli.skills_data")` so it works from editable installs, wheels, and sdists alike.

`pyproject.toml` declares `[tool.setuptools.package-data]` to include `**/*.md` (and any future helper files) inside the wheel. **Do not move the skills out of the package** -- moving them to a repo-root `skills/` directory would break PyPI installs.

To add a new skill: drop a new directory under `n8n_cli/skills_data/<skill-name>/` with a `SKILL.md` containing YAML frontmatter (`name`, `description`, `user_invocable: true`). Bump the README skill table and the version in both `pyproject.toml` and `n8n_cli/__init__.py`.

## Skill design principles

When adding new skills, follow these conventions to keep them consistent:

1. **Read-only by default.** Destructive operations (delete, bulk modify) require explicit confirmation. Skills like `/n8n-cli-cleanup` and `/n8n-cli-impact` are designed to surface findings without ever applying them.
2. **Always show a dry-run before mutations.** `/n8n-cli-bulk` is the canonical example.
3. **Multi-profile aware.** Skills that target a specific n8n instance should respect the user's `--profile` selection and never mix data across profiles.
4. **Pair with existing skills.** New skills should reference complementary ones (e.g. `/n8n-cli-impact` uses `/n8n-cli-deps` data; `/n8n-cli-replay` produces fixtures for `/n8n-cli-test-fixtures`).
5. **Output format: human-readable by default, JSON via `--json` when piping.**
6. **Cache expensive scans.** Skills that walk every workflow (deps, node-usage) should cache results in `~/.cache/n8n-cli/` so repeat invocations are fast.

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

## Workflow JSON sanitization (important)

The n8n REST API has a strict whitelist for workflow create/update payloads. JSON returned from `wf get` or `wf export` includes many read-only fields (`id`, `createdAt`, `meta`, `staticData`, `pinData`, `tags`, `triggerCount`, `versionCounter`, `shared`, `activeVersionId`, etc.) plus `settings` keys (`callerPolicy`, `availableInMCP`, `timeSavedMode`) that are rejected on POST/PUT with `HTTP 400: request/body/settings must NOT have additional properties`.

`n8n_cli/workflows.py` has a `_sanitize_workflow_payload()` helper that's applied automatically inside `import_workflow`, `create_workflow`, and `update_workflow`. It uses a whitelist approach:

- **Top-level whitelist**: `{name, nodes, connections, settings}`
- **Settings whitelist**: `{executionOrder, saveExecutionProgress, saveDataErrorExecution, saveDataSuccessExecution, saveManualExecutions, executionTimeout, errorWorkflow, timezone, callerIds}`

This makes round-trips work transparently: `wf export <id> -o file.json && wf import file.json` produces a valid copy without manual cleanup. **Do not remove this sanitizer** — many skills (template, refactor, migrate, from-cron, from-zapier, from-mcp, meta-monitor) depend on it for round-trip workflows. The sanitizer is idempotent so it's safe on already-clean payloads.

## n8n quirks worth knowing

- **n8n cloud prunes execution history.** The `executions` API only returns the last N executions (typically 7-30 days). "No executions for this workflow" does not mean "this workflow is dead" on cloud. Skills like `/n8n-cli-cleanup`, `/n8n-cli-cost`, and `/n8n-cli-bulk` document this caveat.
- **`wf set-tags` requires at least one tag ID.** It cannot clear all tags. Use `wf clear-tags <id>` (added in v0.4.1) to remove all tags from a workflow.
- **`wf set-tags` REPLACES, not appends.** To add a tag, fetch existing tags first, combine, then set the combined list.
- **`packages list` returns HTTP 404** on n8n's REST API on both cloud and self-hosted. The community-packages endpoint is not part of the public API. Skills that need this info (e.g. `/n8n-cli-upgrade-preflight`) prompt the user manually.
