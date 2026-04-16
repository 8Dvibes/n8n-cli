---
name: n8n-cli-cleanup
description: "Find dead workflows, orphaned credentials, and duplicate webhooks for deletion. Outputs safe-to-delete recommendations. NOT tagging -- use /n8n-cli-tag-governance for that. Use for quarterly hygiene sweeps."
user_invocable: true
---

# /n8n-cli-cleanup — n8n Hygiene & Junk Drawer Triage

Sweep an n8n instance for dead, orphaned, or low-value resources and produce a triage list. **Never delete anything without explicit user confirmation.**

## Procedure

1. **Inventory**:
   - `n8n-cli --json workflows list` (all workflows)
   - `n8n-cli --json workflows list --inactive` (inactive specifically)
   - `n8n-cli --json credentials list` (all credentials)
   - `n8n-cli --json tags list` (all tags)
   - `n8n-cli --json webhooks list` (active webhook URLs)

2. **Find dead workflows** — for each inactive workflow, check the most recent execution:
   - `n8n-cli --json executions list --workflow-id <id> --limit 1`
   - Flag workflows with no executions in the last 30 days as "dead candidates"
   - Flag workflows with NO executions ever as "born dead — likely template/test/abandoned"

3. **Find orphaned credentials** — credentials not referenced by any workflow:
   - **Fast path**: `n8n-cli audit --categories credentials` — n8n's built-in audit returns credentials not used in any workflow AND credentials not used in any active workflow. Use this first.
   - **Slow path** (if you need to cross-reference workflow names): for each credential, walk all workflow JSONs (`wf list` then `wf get <id>` per workflow) to find references
   - Flag credentials with zero references as orphaned

4. **Find duplicate webhooks** — same path or same node config across multiple workflows. Flag pairs as "potential collision".

5. **Find untagged workflows** — workflows with empty tag arrays. Just count them and list the top 10 by node count.

6. **Find archived junk** — workflows in archived state older than 60 days. These are ready for deletion.

## Output format

```
## n8n Cleanup Report — [profile name] — [date]

### Summary
- Total workflows: N (X active, Y inactive, Z archived)
- Total credentials: N (M orphaned)
- Untagged workflows: N
- Estimated cleanup wins: N items

### Dead candidates (no executions in 30+ days)
| Name | ID | Last run | Recommendation |
|------|----|----|----|
| ... | ... | ... | Archive / Delete / Investigate |

### Born-dead workflows (zero executions ever)
[table]

### Orphaned credentials
| Name | Type | Created | Recommendation |
| ... | ... | ... | Delete (no workflows reference it) |

### Archived workflows ready for permanent deletion (60+ days)
[table]

### Untagged workflows
[count + sample]

### Recommended next actions
1. ...
2. ...
```

## Safety rules

- **Never call `delete`, `rm`, or destructive commands automatically.** This skill is read-only by design.
- Surface every finding with a clear recommendation but require explicit user approval before any deletion.
- If the user says "go ahead and delete the dead ones", confirm the count and the names one more time, then delete in batches with progress reporting.

## Tips

- Run with `--profile cloud` and `--profile hostinger` separately if the user has multiple instances — never mix findings across instances.
- A workflow with zero executions might still be valuable (manual-trigger workflows, rarely-used utilities). Flag these but err on the side of "investigate" not "delete".
- Some credentials are shared across workflows that haven't been imported yet — be careful with credential cleanup recommendations on instances that are mid-migration.

## ⚠️ n8n cloud execution retention

n8n cloud prunes execution history (typically 7-30 days depending on plan). When detecting "dead workflows" via `exec list --workflow-id <id>`, an empty result does NOT necessarily mean the workflow is dead — its executions may have been pruned. Cross-reference with the workflow's `triggerCount`, `updatedAt`, and tag/project context before recommending archival or deletion. Always frame findings as "investigate" not "delete" for instances on cloud.
