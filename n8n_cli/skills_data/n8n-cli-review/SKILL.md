---
name: n8n-cli-review
description: "Review n8n workflow changes PR-style with risk ratings. Explains what changed, why it matters, and flags dangers. NOT a raw diff -- use /n8n-diff for that. Use when approving changes before production or after a handoff."
user_invocable: true
---

# /n8n-cli-review — Workflow Change Review

Take two workflow JSON versions (before and after) and produce a code-review-quality diff with human-readable explanations.

## Procedure

1. **Get both versions**:
   - From two file paths
   - From "production vs staging" — `n8n-cli --profile prod wf export <id>` and `n8n-cli --profile staging wf export <id>`
   - From "current vs git history" — read git history of an exported workflow file
   - From "before/after a wf update" — if the user just ran `wf update`, fetch the latest export and compare to the previous local copy

2. **Diff the structure**, not the raw JSON:

   a. **Nodes added** — list new nodes with type, position, key parameters
   b. **Nodes removed** — list removed nodes with what they used to do
   c. **Nodes changed** — for each changed node, show parameter-level diff (not the whole JSON blob)
   d. **Connections changed** — new edges, removed edges, rerouted edges
   e. **Trigger changes** — schedule changed, webhook path changed, etc.
   f. **Credential references changed** — pointing at a different credential
   g. **Active flag changed**

3. **Categorize each change**:
   - 🟢 **Safe** — formatting, descriptions, position-only changes
   - 🟡 **Behavior-affecting** — adds/removes a step, changes parameters
   - 🔴 **Risky** — credential changes, removed error handlers, schedule changes, removed validation steps

4. **Produce a review**:

```markdown
## Workflow Review: [Name]

**Compared:** [version A] vs [version B]
**Summary:** N changes (X safe, Y behavior, Z risky)

### Risk assessment
🔴 1 risky change requires sign-off before applying.
🟡 3 behavior changes — review each.
🟢 5 safe changes — auto-approve.

### Risky changes
1. **[node name]** — credential changed from `Stripe Live` to `Stripe Test`
   - Impact: This workflow will hit the test Stripe environment in production. Confirm this is intentional.
   - Recommendation: Block merge until resolved.

### Behavior changes
2. **[node name]** — added new step that posts to Slack
   - Impact: Slack channel will receive a new message type. Verify the channel can handle it.
3. ...

### Safe changes
- Renamed "Function" → "Calculate Total" (cosmetic)
- Moved "Send Email" node 50px to the right (position only)

### Recommendation
Block merge. The Stripe credential swap looks unintentional. Confirm with the author before applying.
```

## Output format

- Markdown review with risk badges (🟢🟡🔴)
- Compact node-by-node diff format (not raw JSON)
- Clear recommendation: approve / approve with notes / block

## Tips

- For position-only changes (someone dragged a node 50px), don't waste review attention. Group them at the bottom under "cosmetic".
- Credential changes are almost always significant — flag every single one.
- Schedule trigger changes can be production-critical. Always flag.
- Webhook path changes will break upstream callers. Always flag.
- If the diff has 50+ changes, it's probably a rewrite — suggest reviewing as a new workflow rather than as a change.
- For team workflows with a known "owner", suggest @mentioning them in the recommendation.

## Companion modes

- **Multi-environment drift**: "Compare this workflow between cloud and self-hosted" — same skill, just two profiles
- **Git-history review**: "Show me how this workflow changed over the last month" — chain reviews through git history of the exported file
