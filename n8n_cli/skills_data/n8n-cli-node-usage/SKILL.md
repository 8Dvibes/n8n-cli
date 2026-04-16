---
name: n8n-cli-node-usage
description: "Search all n8n workflows for a specific node type, credential, or pattern. Answers 'which workflows use Slack?' Use when an API changes, a node has a breaking update, or you need to find every use of a service."
user_invocable: true
---

# /n8n-cli-node-usage — Search Workflows by Node, Credential, or Pattern

Given a node type, credential type, or arbitrary pattern, find every workflow that uses it.

## Procedure

1. **Parse the search query**:
   - `slack` → search for nodes whose type contains `slack` (Slack, Slack Trigger, etc.)
   - `openai` → same pattern
   - `httpRequest` → exact node type
   - `cred:slackOAuth2Api` → search by credential type
   - `param:url=https://api.stripe.com` → search by parameter value
   - `code:fetch` → search inside Code node JS/Python source for a string

2. **Fetch all workflows**:
   - `n8n-cli --json workflows list` to get the list of IDs
   - For each, `n8n-cli --json wf get <id>` to get the full JSON
   - **Cache** the results in `~/.cache/n8n-cli/workflows-snapshot.json` with a timestamp so repeat searches don't re-fetch

3. **Search**:
   - For each workflow, walk all nodes
   - Match against the parsed query
   - Record: workflow id, workflow name, node name, node type, the matching field

4. **Group results**:
   - By workflow (default) — "these N workflows use this node"
   - By node configuration — "these N nodes are all configured the same way" (useful for finding duplicates)
   - By project / tag — "Slack node usage across projects"

5. **Output**:

```markdown
## Node Usage: "slack"

**Match type:** node type contains "slack"
**Matched workflows:** 12 (out of 47 total)

### Slack node usage
| Workflow | Node name | Node type | Notes |
| Daily Standup | "Post to #general" | n8n-nodes-base.slack | active |
| Order Notify | "Notify ops channel" | n8n-nodes-base.slack | active, in error handler branch |
| ... |

### Slack Trigger usage
| Workflow | Trigger config | Status |
| Slack Listener | listens to /command/foo | active |

### Summary by project
- Production: 8 workflows
- Staging: 3 workflows
- Sandbox: 1 workflow
```

## Output format

- Always show match counts up front (X workflows out of Y total)
- Group by node type sub-category
- For "I'm changing the Slack API" use cases, sort by workflow status (active first, then inactive)

## Tips

- This skill is fast on small instances and slow on large ones (one `wf get` per workflow). Use the snapshot cache aggressively.
- For breaking-API-change scenarios, output a checklist the user can work through: "Update workflow A → done. Update workflow B → done. ..."
- For Code node searches, also offer to grep the Code body for related strings — e.g. searching for `slack` in Code nodes might find `axios.post('https://hooks.slack.com/...)` patterns
- This skill pairs well with /n8n-cli-impact — find usages first, then assess impact of changing them
- Companion query: "find all workflows that use the deprecated XYZ node" — useful for n8n upgrade planning (see /n8n-cli-upgrade-preflight)
