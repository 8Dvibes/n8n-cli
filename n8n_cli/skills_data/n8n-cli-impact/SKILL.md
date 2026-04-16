---
name: n8n-cli-impact
description: "Check blast radius before making n8n changes. Answers 'if I delete credential X or deactivate workflow Y, what breaks?' Use before any destructive operation in production."
user_invocable: true
---

# /n8n-cli-impact — Change Blast-Radius Analysis

Given a proposed change to an n8n instance, find everything that would be affected and report it before the change is made.

## Procedure

1. **Identify the target of the change** — what is the user about to touch?
   - A workflow (delete, deactivate, rename)
   - A credential (delete, rotate, edit)
   - A webhook URL (change path, deactivate the parent workflow)
   - A sub-workflow (delete or change its interface)
   - A tag (delete, merge with another)
   - A node type (across all workflows — relevant if a node version has a breaking change)

2. **Build the dependency graph** (or load it from `~/.cache/n8n-cli/deps.json` if /n8n-cli-deps was run recently):
   - Use the same procedure as /n8n-cli-deps to fetch all workflows + extract refs

3. **Reverse-search** the graph for the target:
   - For each workflow, check whether it references the target
   - Build a list of "affected workflows" with the type of relationship

4. **Categorize impact**:
   - 🔴 **Breaking** — workflow will fail immediately (e.g. deleting a credential that's actively used)
   - 🟡 **Behavior change** — workflow will keep running but do something different (e.g. credential rotated to a different account)
   - 🟢 **Cosmetic** — no functional impact (e.g. tag rename, no behavior change)

5. **Compute downstream effects**:
   - If an affected workflow has its own sub-workflow callers, those are also affected indirectly
   - Recurse one level deep and report indirect impacts

6. **Output a blast-radius report**:

```markdown
## Impact Analysis: [Proposed change]

**Target:** Stripe Live API credential (id: cred_xyz)
**Action:** Delete

### Direct impact: 7 workflows
| 🔴 | Process Order | uses cred for `Charge Customer` step | breaks immediately |
| 🔴 | Refund Order | uses cred for `Stripe Refund` step | breaks immediately |
| 🟡 | Daily Stripe Sync | uses cred for `List Charges` — has fallback to test mode | degrades silently |
| ... |

### Indirect impact: 3 workflows
These call the workflows above as sub-workflows, so they'll fail too:
- Order Fulfillment Pipeline (calls Process Order)
- Customer Lifetime Value (calls Daily Stripe Sync)
- ...

### Affected webhooks
- POST /webhook/stripe-event — handled by Process Order

### Recommendation
🔴 BLOCK. This change breaks 7 workflows immediately. Required steps before proceeding:
1. Create the replacement credential first
2. Update all 7 workflows to use the new credential (use /n8n-cli-bulk)
3. Then delete the old credential

### How to safely apply
[step-by-step playbook]
```

## Output format

- Lead with risk level (🔴🟡🟢) and a one-line summary
- Always show the affected workflow list, sorted by severity
- Always end with a recommended safe-application playbook
- For 🟢 changes, the report is short. For 🔴 changes, surface every detail.

## Safety rules

- This skill is **read-only**. Never apply the change automatically.
- Always present the report and ask for explicit confirmation before suggesting any next step.
- For 🔴 changes, the recommended playbook should always include "create replacement first, migrate, then delete" — never propose the destructive step directly.

## Tips

- For credential rotation, the typical safe flow is: create new credential → update all workflows to point at new → test → delete old. Frame the recommendation that way.
- For webhook URL changes, remind the user that any *external* caller of the webhook will also break — this skill can't see those, so the user needs to know.
- For workflow deletion, also check whether the workflow ID appears as a string anywhere else in the instance (e.g. hardcoded in a Code node). Search broadly.
