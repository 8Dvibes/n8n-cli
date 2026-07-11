# Claude Code Skills

n8n-cli ships with **40 Claude Code skills** — pre-built slash commands that teach Claude Code how to drive n8n-cli for common workflows. Skills live in `n8n_cli/skills_data/<skill-name>/SKILL.md` and are installed into `~/.claude/skills/`.

## Skill Installer

```bash
n8n-cli skills list                        # See bundled skills + install status
n8n-cli skills install                     # Install all 40
n8n-cli skills install n8n-cli-status      # Install one
n8n-cli skills install --force             # Overwrite existing
n8n-cli skills uninstall n8n-cli-status    # Remove a skill
n8n-cli skills path                        # Print install target directory
n8n-cli skills doctor                      # Validate every SKILL.md against the live CLI surface
```

Install target defaults to `~/.claude/skills/`. Override with `CLAUDE_SKILLS_DIR=/some/path n8n-cli skills install`.

The `skills.py` module reads skills via `importlib.resources.files("n8n_cli.skills_data")` so it works from editable installs, wheels, and sdists. The `pyproject.toml` `[tool.setuptools.package-data]` entry includes `**/*.md` and all files inside `skills_data`. **Do not move skills out of the package** — it would break PyPI installs.

### Skills Doctor

`n8n-cli skills doctor` (added in v0.4.1) validates every bundled `SKILL.md` against the live CLI surface. It extracts every `n8n-cli ...` invocation from each skill and checks that the subcommand path and flags reference real CLI commands. Catches typos, drift between docs and code, and copy-paste mistakes.

## Skill Categories (40 total)

### Core Ops (11)

| Skill | What it does |
|---|---|
| `/n8n-cli-status` | Health check, active workflows, recent errors — one-shot dashboard |
| `/n8n-cli-debug` | Pull failed executions, analyze error patterns, suggest fixes |
| `/n8n-cli-create` | Describe a workflow in English, Claude builds it and imports it |
| `/n8n-cli-import` | Import a workflow JSON with guided credential mapping |
| `/n8n-cli-export` | Export workflows to JSON for git, backup, or migration |
| `/n8n-cli-monitor` | Watch the execution stream and alert on failures |
| `/n8n-cli-migrate` | Move workflows between cloud and self-hosted (with credential remapping) |
| `/n8n-cli-backup` | Full instance backup to a git-tracked directory |
| `/n8n-cli-diff` | Compare workflows between instances or against local JSON |
| `/n8n-cli-webhook-test` | Send test payloads to webhook workflows |
| `/n8n-cli-creds` | Credential gap analysis — find what's missing for a workflow |

### Hygiene & Governance (4)

| Skill | What it does |
|---|---|
| `/n8n-cli-cleanup` | Find dead workflows, orphaned credentials, untagged junk — triage list with safe-to-delete recommendations |
| `/n8n-cli-cost` | Execution cost analysis: top consumers, hourly distribution, suspected spammers |
| `/n8n-cli-schedule-audit` | Audit Schedule Triggers across all workflows, find collisions, suggest a rebalanced schedule |
| `/n8n-cli-tag-governance` | Find untagged workflows, propose tags based on content, bulk-apply |

### Authoring & Refactoring (4)

| Skill | What it does |
|---|---|
| `/n8n-cli-document` | Generate human-readable markdown docs from a workflow JSON |
| `/n8n-cli-template` | Convert a workflow into a reusable template, or instantiate from one |
| `/n8n-cli-refactor` | Analyze a workflow for simplification opportunities and propose a refactor |
| `/n8n-cli-review` | PR-style code review of workflow changes with risk badges |

### Dependency Mapping (3)

| Skill | What it does |
|---|---|
| `/n8n-cli-deps` | Build a dependency graph: workflow → sub-workflow → credential → webhook |
| `/n8n-cli-impact` | "If I delete X, what breaks?" — reverse blast-radius analysis |
| `/n8n-cli-node-usage` | Search across all workflows for usage of a specific node, credential, or pattern |

### Production Ops (3)

| Skill | What it does |
|---|---|
| `/n8n-cli-meta-monitor` | Generate a meta-workflow inside n8n that monitors all other workflows and alerts on failures |
| `/n8n-cli-upgrade-preflight` | Pre-flight check before upgrading n8n: deprecated nodes, breaking changes, package compatibility |
| `/n8n-cli-bulk` | Safe bulk ops with mandatory dry-run: activate by tag, archive by age, swap credentials |

### Testing (3)

| Skill | What it does |
|---|---|
| `/n8n-cli-test-fixtures` | Generate realistic test payloads for webhook workflows |
| `/n8n-cli-replay` | Pull a real failed execution, capture its input, replay it deliberately for debugging |
| `/n8n-cli-smoke` | Define and run a smoke-test suite that verifies critical workflows respond correctly |

### Bridge to Other Tools (5)

| Skill | What it does |
|---|---|
| `/n8n-cli-from-mcp` | Convert an MCP server or Claude Code skill into an equivalent n8n workflow |
| `/n8n-cli-to-mcp` | Wrap an n8n workflow as an agent-callable tool (MCP, OpenAI function, Anthropic tool, or HTTP) |
| `/n8n-cli-from-cron` | Read a crontab and generate equivalent n8n workflows for each entry |
| `/n8n-cli-from-launchd` | macOS: read launchd plists and generate equivalent n8n workflows |
| `/n8n-cli-from-zapier` | Migrate a Zapier zap to an equivalent n8n workflow |

### Expert Reference (7)

In-session reference libraries for n8n internals. No CLI commands — Claude consults these as context when writing code or configuring nodes. These skills include multiple supporting `.md` files beyond `SKILL.md`.

| Skill | What it does |
|---|---|
| `/n8n-code-javascript` | JavaScript Code node syntax: `$input`/`$json`/`$node`, `$helpers`, DateTime, run-once vs run-for-each |
| `/n8n-code-python` | Python Code node syntax (beta): `_input`/`_json`/`_node`, stdlib-only constraints |
| `/n8n-expression-syntax` | Expression `{{ }}` syntax: `$json`, `$node`, `$vars`, common mistakes and fixes |
| `/n8n-mcp-tools-expert` | Guide for using n8n-mcp MCP server tools: tool selection, parameter formatting, validation |
| `/n8n-node-configuration` | Operation-aware node property guidance: required fields, property dependencies, common patterns |
| `/n8n-validation-expert` | Fix workflow validation errors: error codes, false positives, credential vs config issues |
| `/n8n-workflow-patterns` | Proven architecture patterns: webhooks, HTTP API integration, AI agents, scheduled tasks, database ops |

## Skill Design Principles

1. **Read-only by default.** Destructive operations (delete, bulk modify) require explicit confirmation. Skills like `/n8n-cli-cleanup` and `/n8n-cli-impact` surface findings without ever applying them.
2. **Always show a dry-run before mutations.** `/n8n-cli-bulk` is the canonical example.
3. **Multi-profile aware.** Skills that target a specific n8n instance should respect `--profile` and never mix data across profiles.
4. **Pair with existing skills.** New skills should reference complementary ones (e.g. `/n8n-cli-impact` uses `/n8n-cli-deps` data; `/n8n-cli-replay` produces fixtures for `/n8n-cli-test-fixtures`).
5. **Output format: human-readable by default, JSON via `--json` when piping.**
6. **Cache expensive scans.** Skills that walk every workflow (deps, node-usage) should cache results in `~/.cache/n8n-cli/` so repeat invocations are fast.

## Adding a New Skill

1. Create a new directory under `n8n_cli/skills_data/<skill-name>/`
2. Add a `SKILL.md` with YAML frontmatter (`name`, `description`, `user_invocable: true`)
3. Bump the README skill table and the version in both `pyproject.toml` and `n8n_cli/__init__.py`
4. Run `n8n-cli skills doctor` to validate the new skill's CLI invocations

The 7 expert reference skills include additional `.md` files (e.g. `COMMON_PATTERNS.md`, `ERROR_PATTERNS.md`, `DATA_ACCESS.md`) that ship as package data alongside `SKILL.md`.
