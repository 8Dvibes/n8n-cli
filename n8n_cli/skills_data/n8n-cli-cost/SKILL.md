---
name: n8n-cli-cost
description: "Analyze n8n execution costs and usage patterns. Finds top consumers, hourly distribution, and triggers firing too often. Use when investigating high usage, before billing reviews, or optimizing execution counts."
user_invocable: true
---

# /n8n-cli-cost — n8n Execution Usage & Cost Analysis

Pull execution counts grouped by workflow and surface the top consumers, suspicious patterns, and obvious wins (triggers firing too often).

## Procedure

1. **Pull a representative slice of executions**:
   - Default window: last 7 days. If the user gives a window ("last 24h", "last month"), use that.
   - `n8n-cli --json executions list --limit 1000` to get a wide sample.
   - For high-volume instances, paginate or filter by status.

2. **Group by workflow**:
   - For each unique workflow ID in the result set, count: total runs, success count, error count, average frequency (runs per hour).
   - Cross-reference with `n8n-cli --json workflows list` to get the workflow name.

3. **Top consumers table**:
   - Top 10 workflows by execution count
   - Top 10 workflows by error count
   - Top 10 workflows by frequency (runs per hour)

4. **Hourly distribution**:
   - Bucket execution timestamps into hour-of-day to see when load peaks
   - Surface "off-hours" surprises (workflows that fire heavy at 3am)

5. **Spammer detection** — flag any workflow running:
   - More than 100 times per hour (probably misconfigured trigger)
   - More than 10 times per minute in any 1-min bucket
   - With 50%+ error rate (failing fast = wasted execution count)

6. **Schedule trigger sanity check** — for each workflow with a Schedule Trigger, fetch the workflow JSON (`n8n-cli --json wf get <id>`), inspect the cron expression, and flag:
   - `* * * * *` (every minute) workflows
   - `*/5 * * * *` or tighter (every 5 min or less) without explicit user intent
   - Cron expressions you can't parse — flag for manual review

## Output format

```
## n8n Cost Analysis — [profile] — last [N] days

### Summary
- Total executions: N
- Success / error / waiting: N / N / N
- Top single workflow: [name] (N executions = X% of total)
- Suspected spammers: N

### Top 10 by execution count
| Rank | Workflow | Executions | Error % | Avg/hr |
|------|----------|------------|---------|--------|
| 1    | ...      | ...        | ...     | ...    |

### Top 10 by error count
[table]

### Hourly distribution
[ASCII bar chart, hour 0-23]

### Spammer flags
| Workflow | Pattern | Recommendation |
|----------|---------|----------------|
| Sync X   | Fires every 60s, 50% errors | Reduce frequency or fix the failing branch first |

### Schedule trigger oddities
| Workflow | Cron | Next run | Notes |
| ...      | ...  | ...      | ... |

### Recommended cost wins
1. ...
2. ...
```

## Tips

- n8n's billing model varies (cloud vs self-hosted). On cloud, "executions" = billed units. On self-hosted, the cost is CPU/RAM/DB writes. Tailor the framing accordingly.
- A "spammer" with 100% success rate at 60s cadence might actually be intentional polling. Always frame as "is this what you wanted?" not "this is broken".
- If the user is on a metered plan and asks for a forecast, multiply the daily average by 30 and show the projected monthly bill in execution units.

## ⚠️ n8n cloud execution retention caveat

n8n cloud only retains the last N executions in its API (varies by plan, typically 7-30 days). The cost analysis in this skill is based on what's currently in the API window, NOT lifetime totals. If a workflow ran 10,000 times last month but its executions have been pruned, this skill won't see them. For accurate billing analysis on cloud, cross-reference with n8n's billing dashboard. For self-hosted, the analysis is more complete because executions are retained until manually pruned.
