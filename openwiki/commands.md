# CLI Command Reference

Entry point: `n8n-cli` (registered as `n8n_cli.cli:main` in `pyproject.toml`). All commands support `--json` for machine-readable output. Use `--profile <name>` to target a specific n8n instance.

## Workflows (`workflows` / `wf`)

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
clear-tags <id>
```

Notes:
- `set-tags` **replaces** all tags, not appends. Fetch existing tags first, combine, then set.
- `set-tags` requires at least one tag ID. Use `clear-tags` (v0.4.1) to remove all tags.
- Import/create/update automatically sanitize the payload via `_sanitize_workflow_payload()` — see [Architecture](architecture/overview.md).

## Executions (`executions` / `exec`)

```
list [--workflow-id ID] [--status error|success|waiting|running|new] [--limit N]
get <id>
retry <id>
delete <id>
stop <id>
```

n8n Cloud prunes execution history (typically 7–30 days). "No executions" does not mean "dead workflow" on cloud.

## Credentials (`credentials` / `creds`)

```
list [--type TYPE] [--limit N]
get <id>
schema <type-name>
create <file.json>
delete <id>
transfer <id> <project-id>
```

`get <id>` falls back to filtering the list endpoint on cloud instances that return HTTP 405 for `GET /credentials/{id}`.

## Tags

```
list [--limit N]
create <name>
get <id>
update <id> <name>
delete <id>
```

## Variables (`variables` / `vars`)

```
list [--limit N]
create <key> <value>
get <id>
update <id> [--key KEY] [--value VALUE]
delete <id>
```

## Projects

```
list [--limit N]
get <id>
create <name>
update <id> <name>
delete <id>
users <id>
```

## Users

```
list [--limit N]
get <id-or-email>
delete <id>
change-role <id> <role>
```

## Community Packages (`packages` / `pkg`)

```
list
install <npm-package-name>
get <name>
update <name>
uninstall <name>
```

`packages list` returns HTTP 404 on the n8n REST API on both cloud and self-hosted. The community-packages endpoint is not part of the public API.

## Nodes (local catalog, auto-updating)

```
search <query>                        Search 543+ nodes by keyword
get <name> [--full]                   Get node details (--full for complete property schema)
list [--group G] [--category C] [--credential C] [--ai-tools] [--limit N]
update                                Force-refresh catalog from npm
info                                  Show cached catalog version
```

The node catalog downloads from official n8n npm packages (`n8n-nodes-base`, `@n8n/n8n-nodes-langchain`) and auto-checks for updates on every use. No n8n instance connection needed. Cached at `~/.n8n-cli/nodes/`.

## Webhooks (`webhooks` / `wh`)

```
list                                  List all webhook URLs from active workflows
test <workflow-id> [--data '{}'] [--method POST]
```

`test` looks up the workflow's webhook node, extracts the path, and sends a request to the `webhook-test` endpoint.

## Skills (Claude Code)

```
list                                  List bundled skills + install status
install [name...] [--force]           Install skills into ~/.claude/skills/
uninstall <name> [name...]            Remove installed skills
path                                  Print install target directory
doctor                                Validate every bundled SKILL.md against the live CLI surface
```

See [Skills](skills.md) for the full skill catalog.

## Other

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

## Global Flags

| Flag | Description |
|------|-------------|
| `--json` | Machine-readable JSON output for piping |
| `--profile <name>` | Use a specific n8n instance profile |
| `-v`, `--version` | Print version |
| `-h`, `--help` | Show help |
