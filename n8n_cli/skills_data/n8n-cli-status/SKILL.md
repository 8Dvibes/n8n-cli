---
name: n8n-status
description: "Health check + execution stats + active workflow summary for n8n instances. Use when checking n8n health, reviewing workflow status, or getting an overview of the n8n instance."
user_invocable: true
---

# /n8n-status — n8n Instance Status & Health Check

Run a comprehensive status check on the connected n8n instance using `n8n-cli`.

## Procedure

1. **Health check**: Run `n8n-cli health` to verify connectivity and auth
2. **Active workflows**: Run `n8n-cli workflows list --active` to show all active workflows
3. **Recent errors**: Run `n8n-cli executions list --status error --limit 10` to surface recent failures
4. **Recent successes**: Run `n8n-cli executions list --status success --limit 5` for context
5. **Credentials**: Run `n8n-cli credentials list` to show available credentials
6. **Tags**: Run `n8n-cli tags list` to show workflow organization

## Output Format

Present a concise dashboard:

```
## n8n Status — [profile name]

Health: OK / ERROR
API URL: ...
Active Workflows: N
Total Credentials: N

### Recent Errors (last 10)
[table of failed executions with workflow name, time, error summary]

### Active Workflows
[table of active workflows]
```

## Multi-Profile Support

If the user asks to check both instances, run with `--profile cloud` and `--profile hostinger` separately.

Default profile is `cloud` (aibuildlab.app.n8n.cloud). Use `--profile hostinger` for the self-hosted VPS instance.

## Tips

- If health check fails with 401, the API key may need rotation
- If there are many errors from the same workflow, flag it as a pattern
- Group errors by workflow when presenting results
