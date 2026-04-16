---
name: n8n-cli-schedule-audit
description: "Audit n8n Schedule Triggers for cron collisions and bad expressions. Finds 50-things-at-3am pileups and suggests rebalanced schedules. Use before going to production, after imports, or when spreading load."
user_invocable: true
---

# /n8n-cli-schedule-audit — Schedule Trigger Audit

Read every workflow's Schedule Trigger, build a calendar view of what fires when, and surface collisions and rebalancing opportunities.

## Procedure

1. **Find scheduled workflows**:
   - `n8n-cli --json workflows list --active` to get active workflows
   - For each, `n8n-cli --json workflows get <id>` and look for nodes with `type` containing `scheduleTrigger` or `cron`
   - Extract the cron expression (or interval config) from the node parameters

2. **Build a unified schedule table**:
   - For each scheduled workflow, normalize the trigger to a cron expression
   - Compute next-fire times for the next 24 hours
   - Build a 24-hour bucket: how many workflows fire in each minute of each hour

3. **Find collisions**:
   - Flag any minute where 5+ workflows fire simultaneously
   - Flag the top 5 most-loaded minutes overall (these are your reliability risks)
   - Flag workflows that share the exact same cron expression

4. **Find sus expressions**:
   - `* * * * *` (every minute) — flag with red unless name contains "monitor" or "watch"
   - `*/1 * * * *` — same as above
   - `0 0 * * *` (midnight UTC) — common dumping ground, often unintentional
   - Any expression with 5 fields where the 5th field is `0` (Sundays only) — confirm the user meant Sundays
   - Any expression that fails to parse — flag for manual review

5. **Suggest a rebalanced schedule** for any minute with 5+ collisions:
   - Spread the colliding workflows across the surrounding 5 minutes
   - Output a "before/after" cron table the user can apply

## Output format

```
## n8n Schedule Audit — [profile] — [date]

### Summary
- Scheduled workflows: N
- Distinct cron expressions: M
- Worst collision: N workflows at HH:MM
- Workflows running every minute: N

### Heat map (next 24 hours)
[ASCII bar: 24 hours, height = count of fires per hour]

### Collision hotspots
| Time   | Count | Workflows |
|--------|-------|-----------|
| 00:00  | 12    | Sync A, Sync B, ... |

### Suspicious expressions
| Workflow | Cron | Reason |
| Foo      | * * * * * | Every minute, 60% error rate |

### Recommended rebalance
| Workflow | Current cron | Proposed cron | Rationale |
| Sync A   | 0 0 * * *    | 5 0 * * *     | Spread 00:00 collision |

### How to apply
For each row in the rebalance table, edit the workflow in the n8n UI or use:
  n8n-cli wf export <id> -o /tmp/workflow.json
  # edit the cron field in /tmp/workflow.json
  n8n-cli wf update <id> /tmp/workflow.json
```

## Tips

- n8n schedule triggers can be configured with simple intervals (every N minutes) OR raw cron. Handle both cases.
- Time zones matter. n8n cron is in the instance's configured TZ — confirm with the user before computing fire times.
- Don't propose rebalances that change the *day* a job runs without flagging it explicitly.
- For instances with hundreds of workflows, this scan is expensive (one `wf get` per workflow). Warn the user and ask if they want to proceed.
