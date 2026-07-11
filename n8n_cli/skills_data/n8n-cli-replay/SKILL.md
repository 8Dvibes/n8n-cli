---
name: n8n-cli-replay
description: "Replay a specific failed n8n execution with its original input data. Reproduces the failure on demand without waiting for the trigger. NOT pattern analysis -- use /n8n-debug for that. Use when reproducing an intermittent bug."
user_invocable: true
---

# /n8n-cli-replay — Replay a Real Execution

Take a specific execution (usually a failure) and reproduce it on demand without waiting for the original trigger.

## Procedure

1. **Get the target execution**:
   - If user gives an execution ID: `n8n-cli --json exec get <id>` to fetch the full execution data
   - If user says "the last failed run of workflow X": `n8n-cli --json exec list --workflow-id <id> --status error --limit 1` then fetch the first result

2. **Extract the input data**:
   - Look at the execution's `data.startData` or equivalent — this is what the trigger received
   - If the trigger was a webhook: the body is what we want
   - If the trigger was a schedule: there's no input, the execution is its own input — note this and offer to retry directly via `exec retry <id>`
   - If the trigger was manual: the input was whatever the user pasted in the n8n UI — capture it

3. **Save the input** to disk:
   - `~/.cache/n8n-cli/replays/<workflow-id>/<execution-id>.json`
   - Include metadata: original execution ID, timestamp, error reason, workflow version at the time

4. **Choose replay mode**:

   a. **Direct retry** (n8n-side): `n8n-cli exec retry <execution-id>` — fastest, runs against the same workflow on the same instance. Caveat: if the workflow has been modified since the failure, the retry runs against the new version.

   b. **Webhook replay** (for webhook-triggered workflows): `n8n-cli wh test <workflow-id> --data "$(cat <saved-fixture>)"`. Lets you tweak the input before replaying.

   c. **Cross-instance replay**: replay against staging instead of prod. Requires the workflow to exist on the target instance (use /n8n-cli-migrate first if not).

5. **Run the replay** in the chosen mode and capture the new execution ID

6. **Compare** the new execution to the original:
   - Did it fail the same way? → real bug, not transient
   - Did it succeed? → transient issue (network, rate limit, race condition)
   - Did it fail differently? → upstream state changed, surface what

## Output format

```markdown
## Replay: execution <original-id>

**Workflow:** [name]
**Original failure:** [error message]
**Timestamp:** [original]
**Captured input:** saved to ~/.cache/n8n-cli/replays/<wf-id>/<exec-id>.json

### Replay attempt
**Mode:** webhook
**New execution:** <new-id>
**Result:** SAME ERROR / DIFFERENT ERROR / SUCCESS

### Diagnosis
[What changed, what's the same, what to do next]

### Save as test fixture?
This input is now a great regression test. Save to tests/<workflow-name>/fixtures/regression-<exec-id>.json?
```

## Tips

- **Side effects warning**: replaying a real production execution means real side effects (real Slack messages, real Stripe charges, real emails). Always confirm with the user before replaying anything that touches external systems.
- For replays involving payments, emails, or other high-risk side effects, default to **staging** replay, not production.
- The most useful replay flow is: "this thing failed once at 3am, let me debug it now" — capture the input, save it, replay it deliberately during debugging.
- After the bug is fixed, save the replay input as a regression fixture (use /n8n-cli-test-fixtures' format) so you can re-run it later to catch regressions.
- For high-volume failed executions, this skill pairs with /n8n-cli-debug (which groups failures by pattern) — debug to find the pattern, replay to reproduce one specific instance.
