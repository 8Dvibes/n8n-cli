---
name: n8n-cli-upgrade-preflight
description: "Pre-flight check before upgrading an n8n instance. Scans for deprecated nodes, breaking-change risks, community packages that might not survive the upgrade, and outputs a 'safe to upgrade?' report. Use before any major n8n version bump."
user_invocable: true
---

# /n8n-cli-upgrade-preflight — n8n Upgrade Risk Assessment

Scan an n8n instance against a target version and produce a report of what's likely to break.

## Procedure

1. **Identify current and target versions**:
   - Ask the user: "What version are you on, and what version are you upgrading to?"
   - If unsure of current version, hint at checking the n8n UI footer or running `n8n-cli health` (which sometimes returns version info)

2. **Pull n8n changelog for the version range**:
   - Recommend the user open https://github.com/n8n-io/n8n/releases for the official changelog
   - Look for "BREAKING CHANGES" sections in each release notes between current and target

3. **Inventory the instance**:
   - `n8n-cli --json workflows list` → all workflows
   - For each workflow, fetch the full JSON
   - Extract every node `type` and `typeVersion` used across all workflows
   - `n8n-cli --json packages list` → community packages installed
   - `n8n-cli --json credentials list` → credential types in use

4. **Cross-reference**:

   a. **Deprecated nodes** — check the inventory against known deprecations in the changelog
   b. **Type version bumps** — nodes where the `typeVersion` is now behind the latest (these usually still work but lose new features)
   c. **Removed credential types** — credentials whose type was removed
   d. **Community packages** — for each installed package, check if it's compatible with the target n8n version (if known)
   e. **Code node syntax** — any Python or JS Code nodes that might break with a runtime upgrade

5. **Build the report**:

```markdown
## n8n Upgrade Pre-flight: vX.Y.Z → vA.B.C

### Summary
- Workflows scanned: N
- Unique node types in use: M
- 🔴 Critical issues: X
- 🟡 Warnings: Y
- 🟢 Compatible: Z

### Critical issues (will break)
1. **Node `n8n-nodes-base.deprecatedFoo` removed in vA.B.C**
   - Used in 4 workflows: ...
   - Migration: replace with `n8n-nodes-base.newFoo`
   - Recommended action: update workflows BEFORE upgrading

2. **Community package `@some/package` not compatible**
   - Installed as: ...
   - Used in: workflow X
   - Recommended action: check the package repo for vA.B.C compatibility, or remove the package and replace its usage

### Warnings (might break, depending on usage)
1. **Code node syntax change** — Python 3.9 deprecated in target version
   - Affected: 3 Code nodes in 2 workflows
   - Recommendation: review and test these specifically after upgrade

### Compatible (no action needed)
- N node types are unchanged between versions
- N credential types are unchanged

### Recommended upgrade path
1. Back up the entire instance first: `n8n-cli skills install n8n-cli-backup && /n8n-cli-backup`
2. Resolve the X critical issues above by updating affected workflows
3. Test the affected workflows manually after the changes
4. Take a fresh snapshot
5. Upgrade n8n
6. Run /n8n-cli-status to verify all active workflows are healthy
7. Watch /n8n-cli-monitor for the next 24 hours
```

## Output format

- Always lead with the critical issue count
- Sort findings by severity
- Always include a recommended upgrade path with specific commands

## Tips

- For minor version bumps (e.g. 1.50 → 1.51), the changelog is short and most reports come back clean. Mention that and don't waste pages on it.
- For major version bumps (e.g. 0.x → 1.x), the report can be long. Offer to save it to a markdown file the user can share with their team.
- Community packages are the highest-risk category — they're maintained by third parties and often lag behind n8n core releases.
- If the user is on n8n cloud, they don't manage the upgrade themselves — n8n cloud handles it. In that case, this skill is still useful for "what should I expect when n8n cloud rolls out vX next week?"
- For self-hosted users, the report is more actionable because they control the upgrade timing.
