---
name: n8n-debug
description: "Pull failed n8n executions, analyze error patterns, and suggest fixes. Use when debugging n8n workflow failures, investigating execution errors, or troubleshooting workflow issues."
user_invocable: true
---

# /n8n-debug — n8n Execution Debugger

Analyze failed executions and suggest fixes using `n8n-cli`.

## Arguments

- `/n8n-debug` — Analyze all recent errors (last 20)
- `/n8n-debug <workflow-id>` — Debug a specific workflow's failures
- `/n8n-debug <execution-id>` — Deep-dive a single execution

## Procedure

### Step 1: Gather Failures

```bash
# All recent errors
n8n-cli executions list --status error --limit 20 --json

# Or for a specific workflow
n8n-cli executions list --workflow-id <ID> --status error --limit 20 --json
```

### Step 2: Analyze Each Failure

For each failed execution, run:
```bash
n8n-cli executions get <execution-id> --json
```

Extract from the JSON:
- `data.resultData.error.message` — the error message
- `data.resultData.error.node` — which node failed
- `data.resultData.runData` — per-node execution results

### Step 3: Pattern Recognition

Group errors by:
1. **Same workflow** — recurring failure pattern
2. **Same node type** — systemic node configuration issue
3. **Same error message** — common root cause

### Step 4: Suggest Fixes

Apply these known n8n patterns when diagnosing:

#### IF Node "Cannot read properties of undefined (reading 'caseSensitive')"
- IF node needs `options.version: 2` in conditions structure

#### Execute Workflow "No information about the workflow to execute found"
- Workflow ID must use resource locator format: `{__rl: true, value: "ID", mode: "id"}`
- Plain string workflow IDs DO NOT work

#### Slack "Node does not have any credentials set for slackOAuth2Api"
- Credential key must match authentication type:
  - `slackApi` + `accessToken` OR `slackOAuth2Api` + `oAuth2`
  - Mismatched keys cause credential-not-found errors even when credential exists

#### Agent node expressions showing as literal text
- Expressions in agent prompts need `=` prefix with backtick template literals
- Wrong: `{{ $json.field }}` — Right: `` =`${$json.field}` ``

#### JSON Parser "A Model sub-node must be connected"
- `autoFix: true` requires an LLM connected via `ai_languageModel` connection

#### Gmail reply not threading
- Both `threadId` AND `inReplyTo` are required for proper threading

#### Slack message data missing
- Long messages get split by Slack API (>4000 chars)
- Put critical identifiers at START of messages, not end
- Concatenate all thread messages before parsing

## Output Format

```
## n8n Debug Report

### Error Pattern: [description]
Affected: [workflow name(s)]
Count: N failures in last 24h
Node: [failing node name and type]
Error: [error message]

**Root Cause:** [analysis]
**Fix:** [specific steps]

---
[repeat for each pattern]
```
