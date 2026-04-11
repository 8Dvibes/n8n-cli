---
name: n8n-import
description: "Import n8n workflow JSON with guided credential mapping. Use when importing workflows from files, repos, or other n8n instances."
user_invocable: true
---

# /n8n-import — Import n8n Workflow with Credential Mapping

Import a workflow JSON file into n8n with guided credential resolution.

## Arguments

`/n8n-import <path-to-workflow.json>` — Import a workflow file
`/n8n-import <path-to-workflow.json> --activate` — Import and activate

## Procedure

### Step 1: Read and Analyze the Workflow

```bash
# Read the workflow file to understand what it needs
cat <file.json> | python3 -c "
import sys, json
wf = json.load(sys.stdin)
print(f\"Name: {wf.get('name', 'untitled')}\")
print(f\"Nodes: {len(wf.get('nodes', []))}\")
for n in wf.get('nodes', []):
    creds = n.get('credentials', {})
    if creds:
        for ctype, cref in creds.items():
            print(f\"  Needs: {ctype} -> {cref.get('name', 'unnamed')} (ID: {cref.get('id', 'none')})\")
"
```

### Step 2: Map Credentials

```bash
# List available credentials on the target instance
n8n-cli credentials list --json
```

Compare credential types needed by the workflow against what's available.

For each credential gap:
1. Tell the user which credential type is missing
2. Suggest creating it in the n8n UI (Settings > Credentials)
3. Offer to update the workflow JSON with the correct credential IDs after creation

### Step 3: Update Credential References (if needed)

If the user provides credential mappings, update the JSON:
- Replace credential `id` fields with the correct IDs from the target instance
- Keep credential `name` fields updated to match
- **CRITICAL**: Match credential key to authentication type:
  - `slackApi` goes with `accessToken` auth
  - `slackOAuth2Api` goes with `oAuth2` auth

### Step 4: Import

```bash
# Import (inactive by default)
n8n-cli workflows import <file.json>

# Or import and activate
n8n-cli workflows import <file.json> --activate
```

### Step 5: Verify

```bash
n8n-cli --json workflows get <new-id>
```

## Output

Report:
1. Workflow name and ID
2. Number of nodes imported
3. Credential status (mapped / missing / needs manual setup)
4. Active/inactive status
5. Direct link: `https://aibuildlab.app.n8n.cloud/workflow/<id>`
