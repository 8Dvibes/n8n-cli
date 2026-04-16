---
name: n8n-cli-refactor
description: "Refactor an n8n workflow for simplification. Finds redundant nodes, batching opportunities, and over-complex Code nodes, then proposes a cleaner version. Use when a workflow feels unwieldy or has grown past 20 nodes."
user_invocable: true
---

# /n8n-cli-refactor — AI-Assisted Workflow Refactoring

Read a workflow, identify simplification opportunities, propose a refactor, and (with approval) build the refactored version.

## Procedure

1. **Get the workflow**:
   - `n8n-cli wf export <id> -o /tmp/before.json`

2. **Analyze for refactor opportunities**:

   a. **Redundant nodes** — sequential Set or Function nodes that could combine into one
   b. **Repeated HTTP requests** — multiple HTTP Request nodes hitting the same API. If they're fetching different IDs, propose batching with `Split In Batches` or moving the call into a single node with a loop
   c. **Branch + Merge that does nothing** — IF nodes that split for no reason and immediately re-merge
   d. **Over-complex Code nodes** — JS/Python code blocks doing things n8n nodes already do (HTTP requests via fetch, JSON parsing, date math). Offer to replace with built-in nodes
   e. **Hardcoded magic strings** — URLs, IDs, channel names that should be variables or env config
   f. **Missing error handlers** — risky nodes (HTTP, external API) without error output wired up
   g. **Dead branches** — nodes that aren't connected to anything downstream

3. **Score the refactor opportunities** by impact:
   - High: removes 5+ nodes, fixes a real failure mode
   - Medium: removes 2-4 nodes, reduces complexity
   - Low: cosmetic, single-node consolidation

4. **Propose the refactor** as a side-by-side:

```
## Refactor Proposal: [Workflow Name]

### Current state
- Nodes: 32
- Branches: 4
- Code nodes: 7
- HTTP Request nodes: 8

### Proposed state
- Nodes: 22 (-10)
- Branches: 3 (-1)
- Code nodes: 3 (-4)
- HTTP Request nodes: 5 (-3)

### Changes
1. Combine "Set Customer Vars" + "Set Order Vars" + "Set Defaults" into a single Set node (save 2 nodes)
2. Replace Code node "fetchOrderData" with HTTP Request node + JSON parse — n8n handles this natively (save 1 node + complexity)
3. Remove dead branch "Notify Legacy System" — it's not connected to a final output
4. Add error handler to "Stripe Webhook" — currently any failure here drops the order silently
5. ...

### Risk
- Low: changes 1, 2, 3 are safe
- Medium: change 5 modifies the order of operations slightly
- High: none

### Recommendation
Apply changes 1-3 immediately. Review change 5 with the workflow owner before applying.
```

5. **If user approves**: write the refactored workflow JSON, save to `/tmp/after.json`, then either:
   - **Test mode**: `n8n-cli wf create /tmp/after.json` to import as a NEW workflow (so the original is preserved). Name it "[Original Name] - REFACTOR".
   - **Replace mode**: `n8n-cli wf update <id> /tmp/after.json` (only after explicit confirmation, with the original saved as `/tmp/before.json` for rollback)

## Output format

- Lead with the score (how much complexity is removed)
- Show the side-by-side
- List changes in priority order (do the safe ones first)
- Always save a backup of the original before any update

## Safety

- Never apply a refactor without explicit user approval AND a backup of the original
- For refactors that change the *behavior* (not just the structure) of the workflow, flag explicitly: "this changes what the workflow does in case X — confirm this is intentional"
- If the workflow is currently active, suggest deactivating before refactoring, refactoring, testing manually, then reactivating

## Tips

- The biggest wins are usually replacing Code nodes with built-in nodes (HTTP, Set, Merge) — saves complexity and makes the workflow visible in the n8n UI
- Don't refactor working workflows aggressively. "Slightly more elegant" is not a good reason to risk breaking production.
- For workflows the user inherited and doesn't fully understand, *document first* (use /n8n-cli-document), then consider refactoring.
