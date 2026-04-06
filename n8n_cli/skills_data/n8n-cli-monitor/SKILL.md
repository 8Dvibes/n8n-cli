---
name: n8n-monitor
description: "Watch n8n execution stream and alert on failures. Use when monitoring n8n workflows, watching for errors, or setting up failure alerts."
user_invocable: true
---

# /n8n-monitor — n8n Execution Monitor

Watch the n8n execution stream and surface failures with context.

## Arguments

- `/n8n-monitor` — Check for new errors since last check
- `/n8n-monitor --watch` — Continuous monitoring (poll every 60s)
- `/n8n-monitor --workflow-id <id>` — Monitor a specific workflow
- `/n8n-monitor --slack` — Post failure alerts to Gigawatt Lounge

## Procedure

### One-Shot Check

```bash
# Get recent executions
n8n-cli executions list --status error --limit 20 --json

# For each error, get details
n8n-cli executions get <id> --json
```

Analyze and present:
- Which workflows are failing
- How frequently (error rate)
- What the errors are
- Whether they're new or recurring

### Continuous Watch Mode

Poll every 60 seconds:

```bash
while true; do
    # Get errors from last 2 minutes
    n8n-cli executions list --status error --limit 5 --json
    # Compare against last known state
    # Alert on new failures
    sleep 60
done
```

### Slack Alerting

When `--slack` flag is used, post to Gigawatt Lounge (C0AM2BVMHRT) on new failures:

```
:rotating_light: *n8n Workflow Failure*

*Workflow:* [name] (ID: [id])
*Execution:* [exec-id]
*Error:* [error message]
*Node:* [failing node]
*Time:* [timestamp]
```

Use the Slack MCP server's `slack_post_message` tool to post.

**Slack formatting rules:** No em dashes, no `\!`, keep it clean.

## Output Format

```
## n8n Monitor Report — [timestamp]

### Errors (last hour)
| Workflow | Errors | Last Error | Node |
|----------|--------|-----------|------|
| ...      | N      | message   | name |

### Error Rate
- Total executions: N
- Failures: N (N%)
- Most failing: [workflow name] (N errors)

### Recommendations
- [actionable fix suggestions based on error patterns]
```

## Tips

- Error patterns often indicate credential expiry, API rate limits, or upstream service issues
- If the same workflow fails repeatedly with the same error, it likely needs a code fix
- If many different workflows fail simultaneously, check n8n instance health or network
