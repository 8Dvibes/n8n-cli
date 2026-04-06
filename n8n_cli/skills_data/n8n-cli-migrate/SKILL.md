---
name: n8n-migrate
description: "Migrate n8n workflows between instances (cloud <-> self-hosted). Exports, remaps credentials, and imports. Use when moving workflows between n8n instances."
user_invocable: true
---

# /n8n-migrate — Migrate Workflows Between n8n Instances

Move workflows from one n8n instance to another with credential remapping.

## Arguments

- `/n8n-migrate <workflow-id> --from cloud --to hostinger`
- `/n8n-migrate --all --from cloud --to hostinger`

## Procedure

### Step 1: Export from Source

```bash
# Single workflow
n8n-cli --profile <source> workflows export <id> -o /tmp/migrate-wf.json

# All workflows
n8n-cli --profile <source> --json workflows list > /tmp/migrate-list.json
# Then export each one
```

### Step 2: Map Credentials

```bash
# List credentials on both instances
n8n-cli --profile <source> --json credentials list > /tmp/creds-source.json
n8n-cli --profile <target> --json credentials list > /tmp/creds-target.json
```

Compare credential types between instances. For each credential referenced in the workflow:
1. Find the matching credential type on the target instance
2. If a match exists, update the credential ID in the workflow JSON
3. If no match, flag it for manual creation

### Step 3: Clean and Import

Strip source-specific fields from the workflow JSON:
- Remove `id`, `createdAt`, `updatedAt`, `versionId`
- Update credential references to target instance IDs
- Keep everything else intact

```bash
n8n-cli --profile <target> workflows import /tmp/migrate-wf-remapped.json
```

### Step 4: Verify

```bash
n8n-cli --profile <target> workflows get <new-id>
```

## Available Profiles

- `cloud` — aibuildlab.app.n8n.cloud
- `hostinger` — n8n.srv761271.hstgr.cloud

## Output

Report for each migrated workflow:
- Source ID -> Target ID
- Credential mapping results (matched / missing / needs setup)
- Active/inactive status
- Any warnings (missing nodes, version mismatches)
