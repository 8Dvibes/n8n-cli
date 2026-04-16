---
name: n8n-cli-meta-monitor
description: "Build a self-monitoring workflow inside n8n that alerts on failures via Slack/Discord/email. Creates an actual n8n workflow -- NOT a CLI watcher (use /n8n-monitor for that). Use when setting up always-on observability."
user_invocable: true
---

# /n8n-cli-meta-monitor — Build a Self-Monitoring Workflow

Create a workflow inside n8n that watches all the *other* workflows and alerts when something breaks. The meta-workflow becomes your reliability layer for n8n itself.

## Procedure

1. **Gather requirements** by asking the user:
   - Where should alerts go? (Slack channel, Discord webhook, email, all of the above)
   - What's the alert threshold? (default: any new failure, or N failures in M minutes)
   - How often should the monitor run? (default: every 5 minutes)
   - Should it check all workflows or only ones with a specific tag? (default: all active workflows)
   - Should it use the n8n API directly or shell out to `n8n-cli`? (default: API for portability)

2. **Build the meta-workflow JSON** with this structure:

   - **Schedule Trigger** — runs every N minutes
   - **HTTP Request** node hitting `/api/v1/executions?status=error&limit=20` (with API key from credential)
   - **Code node** that:
     - Reads `~/.cache/n8n-cli/last-seen-execution-id` (or stores state in n8n's variables)
     - Filters to only NEW executions since last check
     - Groups by workflow ID, counts failures
     - Returns a list of "alert items"
   - **IF node** that branches: any new failures? → notify, else → exit
   - **Slack** (or Discord, or Email) node that posts the alert with workflow name, error count, link to the n8n UI
   - **Set Variable** node that updates "last-seen-execution-id" for next run

3. **Build a sensible alert payload**:
   ```
   :warning: n8n alert: 3 new failures since last check (5 min ago)

   • Workflow "Daily Stripe Sync" — 2 failures
     Last error: HTTP 429 from api.stripe.com (rate limit)
     https://yourinstance.n8n.cloud/workflow/abc123

   • Workflow "Order Webhook" — 1 failure
     Last error: timeout after 30s
     https://yourinstance.n8n.cloud/workflow/xyz789

   Run /n8n-cli-debug to investigate.
   ```

4. **Save the workflow JSON** to `/tmp/meta-monitor.json`, then:
   - `n8n-cli wf import /tmp/meta-monitor.json` (don't activate by default)
   - Print the new workflow ID and a manual-run command for testing
   - Walk the user through testing it: trigger one of their workflows manually with bad input, confirm the alert fires
   - Then activate: `n8n-cli wf activate <id>`

5. **Document the meta-workflow** itself using /n8n-cli-document so future maintainers understand it

## Output format

- Confirm each requirement before building
- Show the workflow JSON structure (high-level, not raw JSON)
- Walk the user through the test → activate flow

## Tips

- The meta-workflow needs an n8n API credential. Walk the user through creating one if it doesn't exist.
- For instances with 1000+ workflows, paginate the API call. The default `--limit 20` is fine for most.
- State management: storing "last-seen-execution-id" in n8n's `variables` API is more portable than writing to disk. Default to that.
- Don't spam alerts. Always include a "deduplication window" (don't re-alert on the same workflow within 30 min) to avoid alert fatigue.
- For Slack alerts, use blocks (rich formatting) not plain text — much more readable. For Discord, use embeds.
- If the user already has a Datadog/Grafana/etc. monitoring stack, suggest sending alerts there too via webhook.

## Companion: meta-meta-monitor

If the user wants belt-and-suspenders, the meta-monitor can be checked by an *external* probe (cron job on a different machine that hits the n8n API and verifies the meta-monitor ran in the last N minutes). That's a different skill — call it out as a future addition.
