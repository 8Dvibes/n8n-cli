# n8n-cli — Quickstart

**n8n-cli** is a scriptable, pipeable CLI for the n8n REST API. Zero external dependencies (Python 3.9+ stdlib only). 80+ commands covering workflows, executions, credentials, nodes, tags, variables, projects, users, webhooks, security audits, and more. Ships with 40 Claude Code skills.

Published to PyPI as `n8n-toolkit`. Built by [AI Build Lab](https://aibuildlab.com).

## Install

```bash
pip install n8n-toolkit
```

Or from source:

```bash
git clone https://github.com/8Dvibes/n8n-cli.git
cd n8n-cli
pip install .
```

## Quick Start

```bash
# Configure your n8n instance
n8n-cli config set-profile cloud --url "https://your-instance.app.n8n.cloud/api/v1" --key "your-api-key" --default

# Or use environment variables
export N8N_API_URL="https://your-instance.app.n8n.cloud/api/v1"
export N8N_API_KEY="your-api-key"

# Check connection
n8n-cli health

# List workflows
n8n-cli workflows list --active

# Export / Import
n8n-cli workflows export <id> -o workflow.json
n8n-cli workflows import workflow.json --activate
```

## Configuration

Config is stored at `~/.n8n-cli.json` (mode 600). Environment variables take priority over config file values:

| Variable | Description |
|----------|-------------|
| `N8N_API_URL` | n8n API base URL |
| `N8N_API_KEY` | API key |
| `N8N_PROFILE` | Profile name to use |

Supports multiple named profiles for different n8n instances (cloud + self-hosted). Switch with `--profile <name>` or `n8n-cli config use <name>`.

See [Commands](commands.md) for the full CLI reference.

## Claude Code Skills

n8n-cli bundles 40 Claude Code skills — pre-built slash commands that teach Claude Code how to drive n8n-cli. Install them with:

```bash
n8n-cli skills install          # all 40
n8n-cli skills install n8n-cli-status  # just one
n8n-cli skills list             # see what's bundled + installed
```

See [Skills](skills.md) for the full catalog and skill design principles.

## JSON Output

Add `--json` to any command for machine-readable output:

```bash
n8n-cli --json workflows list --active | jq '.[].name'
n8n-cli --json executions list --status error | jq length
```

## Documentation Sections

- [Architecture](architecture/overview.md) — Module structure, design decisions, API client, config, workflow sanitization
- [Skills](skills.md) — 40 Claude Code skills across 8 categories, installer, doctor validation
- [Commands](commands.md) — Full CLI command reference by resource type
