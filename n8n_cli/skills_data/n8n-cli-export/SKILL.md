---
name: n8n-export
description: "Export n8n workflows to JSON for version control, backup, or migration. Use when backing up workflows, exporting for git, or migrating between instances."
user_invocable: true
---

# /n8n-export — Export n8n Workflows

Export one or more workflows to JSON files for version control or backup.

## Arguments

- `/n8n-export <workflow-id>` — Export a single workflow
- `/n8n-export --all` — Export all workflows
- `/n8n-export --active` — Export all active workflows
- `/n8n-export --tag <tag-name>` — Export workflows with a specific tag

## Procedure

### Single Workflow Export

```bash
n8n-cli workflows export <id> -o <output-path>.json
```

Default output path: `./n8n-workflows/<workflow-name>.json`

### Bulk Export

```bash
# Get list of workflow IDs
n8n-cli workflows list --json [--active] [--tag TAG] > /tmp/n8n-wf-list.json

# Export each one
python3 -c "
import json, subprocess, re
with open('/tmp/n8n-wf-list.json') as f:
    workflows = json.load(f)
for wf in workflows:
    wid = wf['id']
    name = re.sub(r'[^a-zA-Z0-9_-]', '_', wf.get('name', 'untitled'))
    path = f'n8n-workflows/{name}_{wid}.json'
    subprocess.run(['n8n-cli', 'workflows', 'export', wid, '-o', path])
    print(f'Exported: {path}')
"
```

### For Git Version Control

Create a clean export directory:
```bash
mkdir -p n8n-workflows/
# Export all active workflows
# Strip volatile fields (versionId, updatedAt) for cleaner diffs
```

## Output

- Confirm each exported file path and size
- Total count of workflows exported
- Suggest `git add` if in a git repo

## Tips

- Exported JSON includes everything: nodes, connections, settings, credentials (IDs only, no secrets)
- For migration between instances, use `/n8n-import` on the target instance
- Credential IDs will need remapping when importing to a different instance
