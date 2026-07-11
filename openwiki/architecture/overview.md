# Architecture Overview

## Module Map

```
n8n_cli/
  cli.py                 — argparse CLI entrypoint, all subcommand routing
  client.py              — urllib-based REST client (GET/POST/PUT/PATCH/DELETE + pagination)
  config.py              — Multi-profile config (~/.n8n-cli.json) with env var overrides
  skills.py              — Bundled Claude Code skills installer (list/install/uninstall/path/doctor)
  skills_data/           — 40 skill directories, each with SKILL.md (+ optional reference docs)
  workflows.py            — Workflow CRUD + export/import/activate/archive/transfer/tags
  executions.py           — Execution history, retry, stop, error analysis
  credentials.py          — Credential listing + schema lookup + create/delete/transfer
  nodes.py                — Auto-updating node catalog from npm (543+ nodes)
  webhooks.py             — Webhook URL discovery + test payloads
  tags.py                 — Tag CRUD
  variables.py            — Variable CRUD
  projects.py             — Project management
  users.py                — User management
  audit.py                — Security audit reports
  source_control.py      — Source control pull
  community_packages.py   — Community package management
  __init__.py             — Version string (currently 0.4.2)
```

## Design Decisions

### Zero Dependencies

Only Python stdlib. No `requests`, no `click`, no `rich`. HTTP is done via `urllib.request`, argument parsing via `argparse`, JSON via `json`. This keeps n8n-cli installable everywhere without conflicts. The project explicitly rejects adding external dependencies — contributors should maintain this constraint.

### Multi-Profile Configuration

Config lives at `~/.n8n-cli.json` (written with mode 600). Supports named profiles for different n8n instances. Resolution priority (`config.py`):

1. Environment variables (`N8N_API_URL`, `N8N_API_KEY`)
2. Named profile from config file (selected via `--profile` or `N8N_PROFILE`)
3. Default profile from config file

### API Client

`N8nClient` (`client.py`) wraps the n8n public REST API. Key details:

- Auth: `X-N8N-API-KEY` header on every request
- Timeout: 30 seconds per request
- SSL: default context (`ssl.create_default_context()`)
- Error handling: `N8nApiError` exception with status code, message, and parsed body
- Cursor-based pagination: `paginate()` method auto-fetches all pages (max 250 per page) using the `nextCursor` response field and `cursor` query param

### Workflow Payload Sanitization

The n8n REST API has a strict whitelist for workflow create/update payloads. JSON returned from `wf get` or `wf export` includes many read-only fields (`id`, `createdAt`, `meta`, `staticData`, `pinData`, `tags`, `triggerCount`, `versionCounter`, `shared`, `activeVersionId`, etc.) plus non-accepted `settings` keys that cause HTTP 400 on POST/PUT.

`workflows.py` has a `_sanitize_workflow_payload()` helper applied automatically inside `import_workflow`, `create_workflow`, and `update_workflow`. It uses a whitelist approach:

- **Top-level whitelist**: `{name, nodes, connections, settings}`
- **Settings whitelist**: `{executionOrder, saveDataProgress, saveDataErrorExecution, saveDataSuccessExecution, saveManualExecutions, executionTimeout, errorWorkflow, timezone, callerIds}`

This makes round-trips work transparently: `wf export <id> -o file.json && wf import file.json` produces a valid copy without manual cleanup. The sanitizer is idempotent. Many skills (template, refactor, migrate, from-cron, from-zapier, from-mcp, meta-monitor) depend on it.

**Do not remove the sanitizer.**

### Node Catalog

`nodes.py` downloads and caches node definitions from official n8n npm packages (`n8n-nodes-base` and `@n8n/n8n-nodes-langchain`). The catalog auto-checks for updates on every use via a single HTTP call to the npm registry. Cached at `~/.n8n-cli/nodes/catalog.json`. No n8n instance connection needed — the node catalog is entirely local/npm-sourced.

### n8n API Quirks

- **Cloud prunes execution history.** The executions API only returns the last N executions (typically 7–30 days). "No executions" does not mean "dead workflow" on cloud.
- **`wf set-tags` replaces, not appends.** To add a tag, fetch existing tags first, combine, then set the combined list. It also requires at least one tag ID — use `wf clear-tags <id>` to remove all tags.
- **`packages list` returns HTTP 404** on both cloud and self-hosted. The community-packages endpoint is not part of the n8n public REST API.

## OpenWiki Integration

OpenWiki regenerates this documentation on demand via `openwiki code --update --print` through a reviewed, gated pipeline. There is no GitHub Actions workflow in this repo — the CLI's self-installed `.github/workflows/openwiki-update.yml` is stripped before commit under our Actions-free policy; changes land through a reviewed PR.
