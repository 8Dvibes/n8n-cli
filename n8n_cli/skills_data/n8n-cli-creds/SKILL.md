---
name: n8n-creds
description: "Credential management and gap analysis for n8n. Lists available credentials, finds what workflows need, identifies gaps. Use when auditing credentials, setting up new workflows, or troubleshooting auth issues."
user_invocable: true
---

# /n8n-creds — Credential Management & Gap Analysis

Audit and manage n8n credentials across workflows.

## Arguments

- `/n8n-creds` — Full credential audit (what exists, what's used, what's missing)
- `/n8n-creds check <workflow-id>` — Check if a workflow has all needed credentials
- `/n8n-creds types` — List all credential types available in n8n
- `/n8n-creds schema <type>` — Show the schema for a credential type

## Procedure

### Full Credential Audit

```bash
# Get all credentials
n8n-cli --json credentials list > /tmp/creds.json

# Get all workflows
n8n-cli --json workflows list > /tmp/workflows.json
```

For each workflow, extract credential references from nodes. Cross-reference against available credentials.

Report:
1. **Available credentials** — what's configured on the instance
2. **In-use credentials** — which workflows reference which credentials
3. **Unused credentials** — configured but not referenced by any workflow (cleanup candidates)
4. **Missing credentials** — workflows that reference credential types not available

### Workflow Credential Check

```bash
n8n-cli --json workflows get <id>
n8n-cli --json credentials list
```

For the specific workflow:
- List every node that needs credentials
- Check if matching credentials exist
- Flag any gaps

### Credential Type Lookup

Use the node catalog to find what credential types a node needs:

```bash
n8n-cli nodes get <node-name>
```

The `credentials` field shows which credential types are required.

For the schema of a specific credential type:
```bash
n8n-cli credentials schema <type-name>
```

### Known Credential Gotchas

From debugging experience (L-20260130-001):

1. **Slack has TWO credential types** that are NOT interchangeable:
   - `slackApi` — Access token, use with `"authentication": "accessToken"`
   - `slackOAuth2Api` — OAuth2, use with `"authentication": "oAuth2"`
   - Using the wrong key causes "Credential does not exist" even when it does

2. **Credential key must match authentication type** in the node config.
   The credential exists but the TYPE must match.

3. **Bot vs User tokens** — Slack bot tokens post as the bot, user tokens post as the human who authorized. Check which one you need.

## Output Format

```
## n8n Credential Audit

### Available (N credentials)
| ID | Type | Name | Used By |
|----|------|------|---------|
| ... | slackOAuth2Api | Slack Bot | 3 workflows |

### Missing (N gaps)
| Workflow | Node | Needs | Status |
|----------|------|-------|--------|
| Email Flow | Gmail Node | gmailOAuth2 | NOT CONFIGURED |

### Unused (N cleanup candidates)
| ID | Type | Name |
|----|------|------|
| ... | httpHeaderAuth | Old API Key |
```
