---
name: n8n-diff
description: "Diff n8n workflow versions side-by-side. Shows structural changes between instances, local files, or backups. NOT a review -- use /n8n-cli-review for risk analysis. Use when checking for drift or auditing what changed."
user_invocable: true
---

# /n8n-diff — Compare n8n Workflows

Diff workflows across instances, against local files, or between versions.

## Arguments

- `/n8n-diff <workflow-id> --cloud --hostinger` — Compare same workflow across instances
- `/n8n-diff <workflow-id> --file local.json` — Compare live vs local file
- `/n8n-diff <workflow-id> --before <backup-dir>` — Compare live vs backup

## Procedure

### Cross-Instance Diff

```bash
# Export from both instances
n8n-cli --profile cloud --json workflows get <id> > /tmp/diff-cloud.json
n8n-cli --profile hostinger --json workflows get <id> > /tmp/diff-hostinger.json
```

Then compare using Python:
- Strip volatile fields (updatedAt, versionId, id) before comparing
- Diff node configurations
- Diff connections
- Diff credentials
- Flag any structural differences (missing nodes, different node types)

### Live vs Local File

```bash
n8n-cli --profile <name> --json workflows get <id> > /tmp/diff-live.json
# Compare against provided local file
```

### Present Differences

Focus on meaningful changes:
1. **Added/removed nodes** — new or deleted nodes
2. **Changed node configs** — parameter changes within nodes
3. **Connection changes** — different wiring between nodes
4. **Credential changes** — different credential references
5. **Settings changes** — workflow-level setting differences

Ignore:
- Timestamps (createdAt, updatedAt)
- Version IDs
- Node positions (cosmetic only)

## Output Format

```
## Workflow Diff: <workflow name>
Source A: cloud (live)
Source B: hostinger (live)

### Nodes
+ Added: "Error Handler" (n8n-nodes-base.errorTrigger)
- Removed: "Old Logger" (n8n-nodes-base.set)
~ Changed: "Slack Post" — channel parameter differs
  cloud:     #general
  hostinger: #alerts

### Connections
~ Changed: "IF" true output
  cloud:     -> "Slack Post"
  hostinger: -> "Email Send"

### Credentials
~ Changed: "Slack Post"
  cloud:     slackOAuth2Api (ID: abc123)
  hostinger: slackApi (ID: xyz789)
```
