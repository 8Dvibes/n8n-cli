# n8n-cli

CLI tool for the n8n REST API. Scriptable, pipeable, zero external dependencies.

## Install

```bash
pip install .
# or for development
pip install -e .
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

## Requirements

- Python 3.9+
- No external dependencies (stdlib only)

## License

MIT
