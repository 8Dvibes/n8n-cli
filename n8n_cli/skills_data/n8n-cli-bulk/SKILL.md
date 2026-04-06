---
name: n8n-cli-bulk
description: "Safely run bulk operations across n8n workflows: activate by tag, deactivate by criteria, archive everything not run in 90 days, transfer workflows between projects, set tags in batch. Always shows a dry-run plan first. Use for housekeeping, project reorgs, or environment migrations."
user_invocable: true
---

# /n8n-cli-bulk — Bulk Workflow Operations

Run safe bulk operations against n8n with mandatory dry-run-first behavior.

## Supported operations

- `activate-by-tag <tag>` — activate all workflows with the given tag
- `deactivate-by-tag <tag>` — opposite
- `archive-by-age <days>` — archive workflows with no executions in N days
- `delete-archived-by-age <days>` — permanently delete archived workflows older than N days (REQUIRES double confirmation)
- `transfer-by-tag <tag> <project-id>` — move all workflows with tag X to project Y
- `set-tags-by-name <pattern> <tag-id> [tag-id...]` — set tags on workflows whose name matches a pattern
- `unset-tag-by-name <pattern> <tag-id>` — remove a tag from workflows matching a name pattern
- `update-credential-by-type <old-cred-id> <new-cred-id>` — swap a credential reference across all workflows that use it

## Procedure

1. **Parse the user's bulk request** into one of the supported operations above
2. **Resolve the target set**:
   - For tag-based ops: `n8n-cli wf list --tag <tag> --json`
   - For age-based ops: list all workflows, then check `executions list --workflow-id <id> --limit 1` for the most recent run
   - For pattern-based ops: list all workflows, filter by name regex
   - For credential-swap ops: use the /n8n-cli-node-usage skill internally to find all workflows using the old credential
3. **Build a dry-run plan**:
   ```
   ## Dry run: archive-by-age 90

   The following 12 workflows will be ARCHIVED (no executions in 90+ days):
   1. Foo (id: abc, last run: 2025-12-01)
   2. Bar (id: def, last run: never)
   ...

   Workflows that will NOT be touched:
   - Baz (last run: 2026-04-01) — within 90 days
   - Qux (already archived) — skipped

   Type CONFIRM to proceed, or ABORT to cancel.
   ```
4. **Wait for explicit confirmation** — the literal string "CONFIRM" or equivalent. Never proceed on a vague "yes" for destructive operations.
5. **Execute the operation in batches**:
   - 5-10 workflows per batch
   - Print progress: `[1/12] archiving Foo... ok`
   - On error, STOP, report what failed, and ask whether to retry, skip, or abort
6. **Report results**:
   - Total: 12
   - Succeeded: 11
   - Failed: 1 (with reason)
   - Skipped: 0
7. **Offer rollback** for reversible operations:
   - For activate/deactivate, easy to reverse — surface the reverse command
   - For archive, easy to reverse with `wf unarchive`
   - For delete, NOT reversible — confirm again before doing it

## Safety rules

- **Mandatory dry-run** before any bulk operation. Never skip the dry-run.
- **Double confirmation** for `delete-archived-by-age` (the only truly destructive op). Print the count, the names, and require a second "yes I understand this is permanent" confirmation.
- **Batch size cap** at 50 per run. If the dry-run shows 100+ workflows, ask the user to confirm they really meant that many.
- **Never bulk-modify production workflows without explicit profile selection** — if the user is on the default profile, confirm the profile name before executing.
- **Credential swaps** are especially risky. Always show which workflows will be modified and offer to do it one at a time.

## Output format

- Lead with the operation name and target count
- Show the dry-run as a numbered list with names AND IDs
- After execution, show a results table
- Include rollback instructions for reversible ops

## Tips

- For credential rotation flows, suggest the safe sequence: create new credential → bulk-update workflows → test → delete old credential
- For project reorgs, suggest doing the move in chunks by tag rather than all at once
- For "deactivate everything tagged dev before going home", that's a great quality-of-life flow — make it a one-liner the user can save
- If the user has 500+ workflows, even the dry-run is slow. Show a progress bar during the dry-run scan.
