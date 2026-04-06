# n8n-cli

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![GitHub release](https://img.shields.io/github/v/release/8Dvibes/n8n-cli)](https://github.com/8Dvibes/n8n-cli/releases)
[![No Dependencies](https://img.shields.io/badge/dependencies-zero-brightgreen.svg)](https://github.com/8Dvibes/n8n-cli)

**Scriptable, pipeable CLI for the n8n REST API. Zero external dependencies.**

80+ commands. Auto-updating node catalog (543+ nodes). Multi-instance profiles. Works with n8n Cloud and self-hosted. Ships with 33 Claude Code skills.

![n8n-cli demo](demo.gif)


```
$ n8n-cli workflows list --active
ID                   Active   Name
----------------------------------------------------------------------
0NGypLmiqvKIpwrz     Yes      Gmail: Untrash Email (Multi-Account)
11zReJylAUZeh2ev     Yes      Update Event - Team
1Et6fk45FStEU5qc     Yes      Gmail: Remove Label (Multi-Account)

$ n8n-cli nodes search slack
Node                           Display Name              Description
------------------------------------------------------------------------------------------
slack                          Slack                     Consume Slack API
slackTrigger                   Slack Trigger             Handle Slack events via webhooks

$ n8n-cli --json executions list --status error --limit 3 | jq '.[].id'
"7322"
"7316"
"7310"
```

Built by [AI Build Lab](https://aibuildlab.com) -- teaching context engineering for agentic systems.

## Install

```bash
# From PyPI
pip install n8n-toolkit

# From GitHub
pip install git+https://github.com/8Dvibes/n8n-cli.git

# From source
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
n8n-cli workflows list
n8n-cli workflows list --active
n8n-cli wf ls --tag "production"

# Get workflow details
n8n-cli workflows get <id>

# Export / Import
n8n-cli workflows export <id> -o workflow.json
n8n-cli workflows import workflow.json --activate
```

## Claude Code Skills

n8n-cli ships with **33 [Claude Code skills](https://docs.claude.com/claude-code)** -- pre-built slash commands that teach Claude Code how to drive n8n-cli for common workflows. Once installed, you can type `/n8n-cli-status`, `/n8n-cli-debug`, `/n8n-cli-create` etc. inside any Claude Code session and Claude will execute the right `n8n-cli` commands for you.

```bash
# See what's bundled and what's already installed
n8n-cli skills list

# Install all 33 into ~/.claude/skills/
n8n-cli skills install

# Install just one
n8n-cli skills install n8n-cli-status

# Overwrite existing
n8n-cli skills install --force

# Print the install target
n8n-cli skills path
```

After installing, restart Claude Code (or open a new session) and the slash commands appear in your skill picker.

### Core (the 11 originals)

| Skill | What it does |
|---|---|
| `/n8n-cli-status` | Health check, active workflows, recent errors -- one-shot dashboard |
| `/n8n-cli-debug` | Pull failed executions, analyze error patterns, suggest fixes |
| `/n8n-cli-create` | Describe a workflow in English, Claude builds it and imports it |
| `/n8n-cli-import` | Import a workflow JSON with guided credential mapping |
| `/n8n-cli-export` | Export workflows to JSON for git, backup, or migration |
| `/n8n-cli-monitor` | Watch the execution stream and alert on failures |
| `/n8n-cli-migrate` | Move workflows between cloud and self-hosted (with credential remapping) |
| `/n8n-cli-backup` | Full instance backup to a git-tracked directory |
| `/n8n-cli-diff` | Compare workflows between instances or against local JSON |
| `/n8n-cli-webhook-test` | Send test payloads to webhook workflows |
| `/n8n-cli-creds` | Credential gap analysis -- find what's missing for a workflow |

### Hygiene & governance

| Skill | What it does |
|---|---|
| `/n8n-cli-cleanup` | Find dead workflows, orphaned credentials, untagged junk -- triage list with safe-to-delete recommendations |
| `/n8n-cli-cost` | Execution cost analysis: top consumers, hourly distribution, suspected spammers |
| `/n8n-cli-schedule-audit` | Audit Schedule Triggers across all workflows, find collisions, suggest a rebalanced schedule |
| `/n8n-cli-tag-governance` | Find untagged workflows, propose tags based on content, bulk-apply |

### Authoring & refactoring

| Skill | What it does |
|---|---|
| `/n8n-cli-document` | Generate human-readable markdown docs from a workflow JSON |
| `/n8n-cli-template` | Convert a workflow into a reusable template, or instantiate a new workflow from one |
| `/n8n-cli-refactor` | Analyze a workflow for simplification opportunities and propose a refactor |
| `/n8n-cli-review` | PR-style code review of workflow changes with risk badges |

### Dependency mapping

| Skill | What it does |
|---|---|
| `/n8n-cli-deps` | Build a dependency graph: workflow → sub-workflow → credential → webhook. Output as tree, mermaid, or JSON |
| `/n8n-cli-impact` | "If I delete X, what breaks?" -- reverse blast-radius analysis |
| `/n8n-cli-node-usage` | Search across all workflows for usage of a specific node, credential, or pattern |

### Production ops

| Skill | What it does |
|---|---|
| `/n8n-cli-meta-monitor` | Generate a meta-workflow inside n8n that monitors all your other workflows and alerts on failures |
| `/n8n-cli-upgrade-preflight` | Pre-flight check before upgrading n8n: deprecated nodes, breaking changes, package compatibility |
| `/n8n-cli-bulk` | Safe bulk ops with mandatory dry-run: activate by tag, archive by age, swap credentials, etc. |

### Testing

| Skill | What it does |
|---|---|
| `/n8n-cli-test-fixtures` | Generate realistic test payloads for webhook workflows (happy path + edge + error + security) |
| `/n8n-cli-replay` | Pull a real failed execution, capture its input, replay it deliberately for debugging |
| `/n8n-cli-smoke` | Define and run a smoke-test suite that verifies critical workflows respond correctly |

### Bridge to other tools

| Skill | What it does |
|---|---|
| `/n8n-cli-from-mcp` | Convert an MCP server or Claude Code skill into the equivalent n8n workflow |
| `/n8n-cli-to-mcp` | Wrap an n8n workflow as an agent-callable tool (MCP, OpenAI function, Anthropic tool, or HTTP) |
| `/n8n-cli-from-cron` | Read a crontab and generate equivalent n8n workflows for each entry |
| `/n8n-cli-from-launchd` | macOS-specific: read launchd plists and generate equivalent n8n workflows |
| `/n8n-cli-from-zapier` | Migrate a Zapier zap to an equivalent n8n workflow |

The skills install to `~/.claude/skills/` by default. Override with `CLAUDE_SKILLS_DIR=/some/path n8n-cli skills install`.

## Commands

### Workflows (`workflows` / `wf`)

```
list [--active] [--inactive] [--tag TAG] [--name NAME] [--project-id ID] [--limit N]
get <id>
create <file.json>
update <id> <file.json>
delete <id>
activate <id>
deactivate <id>
export <id> [-o file.json]
import <file.json> [--activate]
archive <id>
unarchive <id>
transfer <id> <project-id>
tags <id>
set-tags <id> <tag-id> [tag-id...]
```

### Executions (`executions` / `exec`)

```
list [--workflow-id ID] [--status error|success|waiting|running|new] [--limit N]
get <id>
retry <id>
delete <id>
stop <id>
```

### Credentials (`credentials` / `creds`)

```
list [--type TYPE] [--limit N]
get <id>
schema <type-name>
create <file.json>
delete <id>
transfer <id> <project-id>
```

### Tags

```
list [--limit N]
create <name>
get <id>
update <id> <name>
delete <id>
```

### Variables (`variables` / `vars`)

```
list [--limit N]
create <key> <value>
get <id>
update <id> [--key KEY] [--value VALUE]
delete <id>
```

### Projects

```
list [--limit N]
get <id>
create <name>
update <id> <name>
delete <id>
users <id>
```

### Users

```
list [--limit N]
get <id-or-email>
delete <id>
change-role <id> <role>
```

### Community Packages (`packages` / `pkg`)

```
list
install <npm-package-name>
get <name>
update <name>
uninstall <name>
```

### Nodes (local catalog, auto-updating)

```
search <query>                        Search 543+ nodes by keyword
get <name> [--full]                   Get node details (--full for complete property schema)
list [--group G] [--category C] [--credential C] [--ai-tools] [--limit N]
update                                Force-refresh catalog from npm
info                                  Show cached catalog version
```

The node catalog downloads from official n8n npm packages and auto-checks for updates on every use. No n8n instance connection needed.

### Webhooks (`webhooks` / `wh`)

```
list                                  List all webhook URLs from active workflows
test <workflow-id> [--data '{}'] [--method POST]
```

### Skills (Claude Code)

```
list                                  List bundled skills + install status
install [name...] [--force]           Install skills into ~/.claude/skills/
uninstall <name> [name...]            Remove installed skills
path                                  Print install target directory
```

### Other

```
health              Check n8n instance connectivity
audit               Generate security audit [--categories credentials,database,filesystem,instance,nodes]
source-control pull Source control pull [--force]
discover            Show API capabilities
config show         Show current profile
config set-profile  Create/update a profile
config list-profiles
config use <name>   Switch default profile
config delete-profile <name>
```

## Multi-Instance Support

```bash
# Set up profiles
n8n-cli config set-profile cloud --url "https://instance.app.n8n.cloud/api/v1" --key "key1" --default
n8n-cli config set-profile selfhosted --url "https://n8n.myserver.com/api/v1" --key "key2"

# Switch between them
n8n-cli --profile selfhosted workflows list
n8n-cli --profile cloud health

# Or set default
n8n-cli config use selfhosted
```

## JSON Output

Add `--json` to any command for machine-readable output:

```bash
n8n-cli --json workflows list --active | jq '.[].name'
n8n-cli --json executions list --status error | jq length
```

## Config

Config stored at `~/.n8n-cli.json` (mode 600). Environment variables take priority:

| Variable | Description |
|----------|-------------|
| `N8N_API_URL` | n8n API base URL |
| `N8N_API_KEY` | API key |
| `N8N_PROFILE` | Profile name to use |

## Why n8n-cli?

| | n8n-cli | MCP Servers | n8n UI |
|---|---------|-------------|--------|
| Works from any terminal | Yes | No (needs MCP client) | No |
| Pipeable / scriptable | Yes | No | No |
| Multi-instance switching | Yes (`--profile`) | Manual config swap | One at a time |
| Node catalog with search | Yes (543+ nodes, auto-updating) | Depends on server | Built-in |
| Works with any AI agent | Yes (Bash) | Claude Code only | Manual |
| Dependencies | Zero | Node.js + npm | Browser |

## Example Prompts for AI Agents

Don't want to memorize commands? Just tell your AI agent what you need:

> "Check my n8n instance for any failed executions today and tell me what went wrong"

> "Export all my active workflows to a folder for git version control"

> "Build me a workflow that checks a Google Sheet every morning and posts a summary to Slack"

> "Run a security audit and tell me which credentials aren't being used"

See **[EXAMPLES.md](EXAMPLES.md)** for 13 more copy-paste prompts you can hand to Claude Code, Cursor, Codex, or any AI agent.

## Requirements

- Python 3.9+
- No external dependencies (stdlib only)
- Works with n8n Cloud and self-hosted instances

## Support the Project

If this is useful to you, here's how you can help:
- Star the repo (it helps with discoverability)
- Fork it and try it out
- Share it with your n8n community
- [Sponsor](https://github.com/sponsors/8Dvibes) if you want to support continued development
- File issues or PRs for features you'd like to see

## Contributing

Issues and PRs welcome. This project uses zero external dependencies by design -- please keep it that way.

## License

MIT -- see [LICENSE](LICENSE)

---

Built by **[AI Build Lab](https://aibuildlab.com)** | [Tyler Fisk](https://github.com/8Dvibes) | [@tyfisk](https://x.com/tyfisk)
