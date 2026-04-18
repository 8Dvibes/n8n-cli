---
name: n8n-cli-document
description: "Generate human-readable markdown docs from an n8n workflow JSON. Covers trigger, steps, credentials, and failure modes. Use when documenting workflows for team handoff, audits, or onboarding."
user_invocable: true
---

# /n8n-cli-document — Generate Human-Readable Workflow Docs

Take an n8n workflow and produce markdown documentation a human can read without opening the n8n UI.

## Procedure

1. **Get the workflow JSON**:
   - If the user gives a workflow ID: `n8n-cli --json wf get <id>` (or `wf export <id> -o /tmp/wf.json`)
   - If the user gives a file path: read it directly
   - If the user gives a name: `n8n-cli --json wf list --name "..."` to find the ID first

2. **Parse the structure**:
   - Trigger: find the start node(s). Note type (webhook, schedule, manual, etc.) and config (URL path, cron, etc.)
   - Nodes: walk the connections graph from triggers forward
   - For each node, extract: name, type, key parameters, downstream connections
   - Identify credentials used (by name and type)
   - Identify any sub-workflow calls (`executeWorkflow` nodes)
   - Identify error-handler branches (output 1 vs error output)

3. **Compute summary stats**:
   - Total nodes, branches, error handlers
   - Average path length from trigger to terminal
   - Estimated complexity (low/medium/high based on node count and branching)

4. **Identify failure modes**:
   - Nodes with no error handler attached
   - HTTP requests with no retry logic
   - External API calls that depend on credentials (these are the most common failure points)
   - Hard-coded URLs / IDs / magic numbers

5. **Render the markdown**:

```markdown
# [Workflow Name]

**ID:** `<id>`
**Status:** Active / Inactive
**Project:** ...
**Tags:** ...

## What it does

[2-3 sentence plain-English summary inferred from the trigger, key nodes, and final action]

## How it's triggered

[Trigger type + config. E.g. "Webhook at POST /webhook/foo" or "Daily at 09:00 UTC via Schedule Trigger"]

## Steps

1. **[Node name]** (`[type]`) — [what it does in plain English]
2. ...

(For branching workflows, present as a tree or use sub-bullets per branch)

## Credentials used

| Credential | Type | Used by |
| Slack OAuth | slackOAuth2Api | Notify Channel, Post Update |

## Sub-workflows called

| Workflow | When |
| Send Email | After successful sync |

## Failure modes to watch

- [Node X] has no error handler — failure here will fail the whole run
- [Node Y] depends on credential Z — if it expires, this workflow stops working
- ...

## Operational notes

- Last updated: [date from workflow metadata]
- Recent execution success rate: X% (from the last 50 runs)
- Recent error count: N
```

## Output format

By default, print the markdown to stdout. If the user says "save it", write to:
- `~/n8n-docs/<workflow-name>.md` (sanitize the name)
- Or whatever path the user specifies

## Tips

- For workflows with 30+ nodes, use a hierarchical step list, not a flat one. Group by branch.
- The `description` field on nodes (if set) is gold — use it verbatim where it exists.
- For HTTP Request nodes, surface the actual URL/method in the step description so reviewers can verify what's being called.
- For Code nodes (JS/Python), include the first 3-5 lines of code as context in the step description, but don't dump the whole script.
- For workflows that look auto-generated or trivial (single trigger + single action), skip the deep failure analysis section.

## Companion: bulk documentation

If the user asks "document all workflows in project X", iterate `n8n-cli --json wf list --project-id X`, generate one markdown file per workflow, and offer to commit them to a docs repo.
