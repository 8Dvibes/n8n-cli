---
name: n8n-cli-test-fixtures
description: "Generate realistic test payloads for n8n webhook workflows. Infers input schema and creates happy-path, edge-case, and error fixtures. Use when adding tests to an existing workflow or building one TDD-style."
user_invocable: true
---

# /n8n-cli-test-fixtures — Generate Test Payloads for Webhook Workflows

Read a webhook-triggered workflow, infer the input shape, and generate a set of realistic test payloads (happy path + edge cases + error cases).

## Procedure

1. **Get the workflow**:
   - `n8n-cli --json wf get <id>` (or by name)
   - Confirm it has a webhook trigger node
   - Note the HTTP method, path, and any authentication

2. **Infer the input shape**:
   - Look at the webhook node config: does it specify expected fields, body parser type (JSON, form, raw)?
   - Walk forward to the next nodes — they reference fields from `$json.foo`, `$json.bar`. Those are the fields the workflow uses.
   - For each referenced field, infer the type from how it's used:
     - Used in date math? → date string
     - Used in math? → number
     - Used as a URL? → URL string
     - Used as a recipient? → email
     - Compared to specific strings? → enum (and we know the values)
   - Build a schema-like description of the expected input

3. **Generate fixtures** (3-5 of each):
   - **Happy path** — realistic, all fields present, common values
   - **Edge cases** — empty strings, very long strings, unicode, escaped chars, max numeric values
   - **Error cases** — missing required fields, wrong types, malformed JSON
   - **Security cases** — SQL-injection-y strings, script tags, oversized payloads

4. **Save fixtures** to `tests/<workflow-name>/fixtures/`:
   ```
   tests/
     order-webhook/
       fixtures/
         01-happy-path-standard-order.json
         02-happy-path-international-order.json
         03-edge-empty-customer-name.json
         04-edge-very-long-product-name.json
         05-error-missing-product-id.json
         06-error-invalid-email.json
         07-security-sql-injection.json
   ```

5. **Generate a test runner script** (`tests/<workflow-name>/run.sh`) that loops through the fixtures and posts each one with `n8n-cli wh test`:
   ```bash
   #!/bin/bash
   set -e
   for fixture in fixtures/*.json; do
     echo "▶ $fixture"
     n8n-cli wh test <workflow-id> --data "$(cat $fixture)"
     sleep 1
   done
   ```

6. **Print usage** to the user:
   ```
   Generated 7 fixtures and a runner script in tests/order-webhook/

   Run all tests:    cd tests/order-webhook && bash run.sh
   Run one fixture:  n8n-cli wh test <id> --data "$(cat fixtures/01-happy-path-standard-order.json)"
   ```

## Output format

- List the fixtures generated
- Show the schema you inferred (so the user can correct it if wrong)
- Print the runner usage

## Tips

- For workflows with branching (IF/Switch nodes), generate fixtures that exercise each branch — that's the whole point
- For workflows that read from external state (DB query before processing), the fixtures need to align with that state. Ask the user about preconditions.
- Save the inferred schema as `tests/<workflow-name>/schema.md` so future Claude sessions don't have to re-derive it.
- For security cases, don't actually run them against production — surface the warning and recommend running against staging/sandbox only.
- This skill pairs with /n8n-cli-replay (run a real failed execution as a fixture) and /n8n-cli-smoke (define a smoke-test suite).
