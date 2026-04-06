---
name: n8n-cli-tag-governance
description: "Find untagged workflows, propose a tag taxonomy based on workflow content, and bulk-apply tags. Use when an n8n instance has grown organically and tagging is inconsistent or missing."
user_invocable: true
---

# /n8n-cli-tag-governance — Tag Audit and Taxonomy

Find untagged workflows, suggest tags based on what each workflow actually does, and (with user approval) bulk-apply them.

## Procedure

1. **Inventory tags**:
   - `n8n-cli --json tags list`
   - `n8n-cli --json workflows list` and count tag usage across workflows
   - Flag tags that are used by zero workflows (orphaned tags)
   - Flag tags that look like duplicates ("slack" + "Slack" + "slack-bot")

2. **Find untagged workflows**:
   - From the workflows list, filter to those with empty tag arrays
   - Get the top 20 by node count (these are the "important" untagged ones)

3. **Propose tags for each untagged workflow**:
   - For each untagged workflow, fetch its full JSON (`wf get <id>`)
   - Inspect the node types it uses (Slack, Gmail, OpenAI, HTTP Request, etc.)
   - Inspect the trigger type (webhook, schedule, manual)
   - Inspect the workflow name for keywords
   - Suggest 1-3 tags from the existing taxonomy (or new tags if nothing fits)

4. **Propose taxonomy improvements** if the existing tags are messy:
   - Group similar tags ("slack" / "Slack" / "slack-bot" → consolidate to "slack")
   - Suggest a tag hierarchy (by service: slack, gmail, openai / by purpose: monitoring, sync, alerting / by environment: prod, staging, sandbox)
   - Propose deletion for orphaned tags

5. **Bulk apply** (only with explicit user approval):
   - For each (workflow, proposed tags) pair, `n8n-cli wf set-tags <workflow-id> <tag-id> [tag-id...]`
   - Report results in a table

## Output format

```
## Tag Governance Report — [profile] — [date]

### Current state
- Tags total: N (M orphaned, K duplicates)
- Tagged workflows: N
- Untagged workflows: M (X% of total)

### Existing tags
| Tag | Workflows | Status |
| slack | 12 | OK |
| Slack | 3 | duplicate of slack — recommend merge |

### Untagged workflows (top 20 by complexity)
| Workflow | Nodes | Suggested tags | Reason |
| Foo      | 24    | slack, monitoring | uses Slack node + scheduled |

### Proposed taxonomy
- By service: slack, gmail, openai, ...
- By purpose: monitoring, sync, alerting, ...
- By env: prod, staging, sandbox

### Bulk-apply preview
N workflows will receive tags. Confirm to proceed.
```

## Safety

- Never apply tags without confirmation.
- Never delete tags without confirmation.
- When merging duplicate tags, the destructive step is to remove the old tag from each workflow first, then delete the old tag — order matters.
- If the user has a custom taxonomy already, respect it. Don't propose a totally different scheme.

## Tips

- The richest signal for a workflow's "purpose" is its name + the credential types it uses.
- Slack-, Gmail-, and OpenAI- prefixed workflows are usually named consistently — use the prefix as the primary tag.
- For heavily integrated workflows (10+ services), suggest the *primary* purpose tag, not 10 service tags.
