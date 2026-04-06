---
name: n8n-cli-smoke
description: "Define a smoke-test suite for n8n workflows and run it on demand or after every deploy. Hits webhook endpoints with known-good payloads and verifies expected responses. Use when promoting workflows from staging to prod, after major changes, or as a daily reliability check."
user_invocable: true
---

# /n8n-cli-smoke — n8n Smoke Test Suite

Build and run a smoke-test suite that verifies critical n8n workflows are responding correctly.

## Procedure

### Mode 1: Build the suite

1. **Ask the user which workflows to include**:
   - "Which workflows should be in your smoke suite?" — usually 5-15 critical webhook workflows
   - Or "smoke-test all workflows tagged 'production'" → list and confirm

2. **For each workflow**:
   - Confirm it's webhook-triggered (smoke tests need an entry point we can hit)
   - Get a known-good payload (use existing /n8n-cli-test-fixtures output, or ask the user to paste one)
   - Define the expected response (HTTP 200 + maybe specific fields)
   - Define a max latency (e.g. should respond within 5s)

3. **Save the suite** to `tests/smoke.yml`:
   ```yaml
   suite: production-smoke
   profile: cloud  # which n8n-cli profile to target

   tests:
     - name: order-webhook
       workflow_id: abc123
       payload_file: tests/smoke/payloads/order-webhook.json
       expect:
         status: 200
         max_latency_ms: 5000
         body_contains: ["ok", "order_id"]
       on_failure: alert  # alert | continue | abort

     - name: stripe-event
       workflow_id: def456
       payload_file: tests/smoke/payloads/stripe-event.json
       expect:
         status: 200
         max_latency_ms: 10000
       on_failure: alert
   ```

4. **Save the payloads** to `tests/smoke/payloads/`

5. **Generate a runner script** (`tests/smoke/run.sh`) that reads the YAML, hits each webhook, and reports results

### Mode 2: Run the suite

1. **Read `tests/smoke.yml`**
2. **For each test**:
   - Resolve the workflow ID
   - Load the payload
   - Time the request
   - `n8n-cli wh test <id> --data "$(cat payload.json)"`
   - Check the response status and latency against the expectation
   - Print result: `✓ order-webhook  200 OK  342ms` or `✗ stripe-event  TIMEOUT  >10000ms`
3. **At the end**, print a summary:
   ```
   Smoke suite: production-smoke
   Profile: cloud
   Started: 2026-04-06 12:34:56
   Duration: 4.2s

   Results: 5 passed, 1 failed
   Failed: stripe-event (TIMEOUT)

   Run /n8n-cli-debug to investigate stripe-event.
   ```
4. **Exit code**: 0 if all pass, 1 if any failed (so it can run in CI)

## Output format

- During run: live progress per test
- At end: summary table + recommended next action

## Tips

- Smoke tests are about *liveness*, not correctness. They prove the workflow responds — not that the result is right. Pair with end-to-end integration tests if you need correctness checks.
- Run smoke tests after every workflow update (use it as a deploy gate)
- Run smoke tests as a scheduled n8n workflow itself (very meta — uses /n8n-cli-meta-monitor)
- Keep payloads small and idempotent. Smoke tests shouldn't create real orders, send real emails, or charge real cards. Use sandbox/test endpoints whenever possible.
- For workflows that have side effects, configure the workflow to detect a `_smoke_test: true` flag in the payload and short-circuit before the side effect.
- For instances with both cloud and self-hosted, run two smoke suites (one per profile) and report side-by-side.

## Companion: continuous smoke

- Schedule smoke tests via cron, post results to Slack
- Hook up smoke results to a status page (statuspage.io, etc.)
- Use smoke results as a deploy gate in your CI/CD pipeline
