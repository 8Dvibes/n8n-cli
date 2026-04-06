---
name: n8n-cli-from-launchd
description: "Read macOS launchd plists (~/Library/LaunchAgents and /Library/LaunchDaemons) and generate equivalent n8n workflows for each scheduled job. Use when migrating off launchd-managed scripts onto n8n for visibility, error handling, and observability. macOS-specific sibling to /n8n-cli-from-cron."
user_invocable: true
---

# /n8n-cli-from-launchd — macOS launchd plists → n8n Workflows

macOS uses launchd, not cron, for scheduled tasks. This skill reads launchd property list (plist) files and converts each scheduled job into an equivalent n8n workflow.

## Procedure

1. **Discover launchd jobs**:
   - User-level: `~/Library/LaunchAgents/*.plist`
   - System user agents: `/Library/LaunchAgents/*.plist`
   - System daemons (root): `/Library/LaunchDaemons/*.plist`
   - Currently loaded: `launchctl list` (also shows last exit status)
   - Ask the user which directory to scan, or scan all three

2. **Parse each plist**:
   - Use Python's `plistlib` (stdlib, no deps): `import plistlib; data = plistlib.load(open(path,'rb'))`
   - Extract these keys:
     - `Label` — job identifier (becomes the workflow name suffix)
     - `ProgramArguments` — the command + args (array of strings)
     - `Program` — alternative single-binary form
     - `StartCalendarInterval` — calendar-based schedule (Hour/Minute/Day/Weekday/Month dict, or array of dicts)
     - `StartInterval` — fixed-interval schedule in seconds
     - `RunAtLoad` — runs when loaded (treat as "run on startup")
     - `KeepAlive` — keeps the process running (NOT a scheduled job, flag this)
     - `WorkingDirectory` — cwd for the command
     - `EnvironmentVariables` — env vars dict
     - `StandardOutPath` / `StandardErrorPath` — log destinations
     - `UserName` — user the job runs as

3. **Translate the schedule** to n8n's Schedule Trigger:

   - **`StartCalendarInterval` (single dict)**:
     - `{Hour: 2, Minute: 0}` → cron `0 2 * * *` (daily at 02:00)
     - `{Hour: 2, Minute: 30, Weekday: 1}` → cron `30 2 * * 1` (Mondays at 02:30)
     - `{Day: 1, Hour: 0, Minute: 0}` → cron `0 0 1 * *` (1st of every month)
   - **`StartCalendarInterval` (array of dicts)**: produces multiple cron rules — n8n supports multiple Schedule Trigger rules in one node
   - **`StartInterval` (seconds)**:
     - 60 → cron `* * * * *` (every minute)
     - 300 → cron `*/5 * * * *` (every 5 minutes)
     - 900 → cron `*/15 * * * *` (every 15 minutes)
     - 3600 → cron `0 * * * *` (hourly)
     - For non-cron-friendly intervals (e.g. 200 seconds), use n8n's interval mode: `{interval: [{field: 'seconds', secondsInterval: 200}]}`
   - **`RunAtLoad: true` only (no schedule)**: this isn't really a scheduled job, it's a one-shot. Flag for the user — usually shouldn't migrate to n8n.
   - **`KeepAlive: true`**: this is a daemon, not a scheduled job. Skip it. n8n is not a process supervisor.

4. **Detect command intent** (same logic as `/n8n-cli-from-cron`):
   - `python3 .../foo.py` → Execute Command node OR rebuild as native nodes
   - `bash .../foo.sh` → Execute Command node
   - `curl https://...` → HTTP Request node (n8n-native, preferred)
   - `osascript ...` → Execute Command node (macOS-only)
   - Custom binary → Execute Command node

5. **Translate environment variables**:
   - Each env var in `EnvironmentVariables` becomes an n8n credential or workflow variable
   - **WARNING: many launchd plists contain secrets in plaintext** as env vars. Surface this to the user explicitly:
     "⚠️ Found likely secrets in plist env vars: API_KEY, GRAND_CENTRAL_API_KEY, ... — these should be moved to n8n credentials, not workflow params"
   - Suggest creating n8n credentials for each detected secret BEFORE building the workflow

6. **Add observability**:
   - Error handler branch on each external call
   - Slack/email alert node on failure (suggest a default channel)
   - Optional: log run history (n8n already does this server-side, but if the original launchd job wrote to a file, mention that the n8n version replaces that with the execution history UI)

7. **Generate one workflow per launchd job**:
   - Workflow name: `from-launchd: <Label>` (e.g. `from-launchd: com.aibuildlab.morning-brief`)
   - Save each as JSON
   - Show the user a summary table BEFORE importing (count, names, schedule, command type, secrets detected)
   - Confirm before bulk import

8. **Import** (only after approval):
   - `n8n-cli wf import` for each
   - DO NOT activate by default — let the user verify each in the n8n UI first

9. **Suggest decommissioning the launchd jobs**:
   - DO NOT unload the launchd jobs automatically
   - Print a checklist:
     1. Verify each n8n workflow runs correctly (manual trigger first, then activate)
     2. Run both the launchd version AND the n8n version in parallel for at least 1 day
     3. Compare outputs to confirm parity
     4. Then unload the launchd job: `launchctl unload ~/Library/LaunchAgents/<label>.plist`
     5. Move the plist to `~/.launchd-archive/` instead of deleting (recoverable)

## Output format

- Numbered list of plists found
- For each: schedule, command, env-var summary, secrets detected
- Proposed n8n workflow name and node graph
- Walkthrough one entry at a time for tricky cases
- Bulk import after final approval

## Tips

- launchd is more powerful than cron — it handles things cron can't (RunAtLoad, KeepAlive, throttling, network state). Don't try to migrate everything. Focus on the *scheduled* jobs.
- If the original plist has `StandardOutPath` / `StandardErrorPath`, the n8n equivalent is the execution detail panel — much better than raw log files but a different mental model.
- For jobs that run every few seconds (StartInterval < 60), n8n's Schedule Trigger isn't a great fit. Suggest keeping those in launchd or using a long-running n8n workflow instead.
- For jobs running as `root` from `/Library/LaunchDaemons/`, you need `sudo` to read the plist file. Surface this and ask the user to run the discovery step manually.
- This skill pairs with `/n8n-cli-meta-monitor` — once your launchd jobs are in n8n, you also get failure alerting for free.

## Companion: hybrid mode

For complex launchd jobs (multi-stage shell pipelines, jobs that read launchd-specific signals), the right answer might be: keep them in launchd, but have n8n monitor them via a heartbeat workflow that checks `launchctl print` output. Surface this option for jobs that don't translate cleanly.

## Example end-to-end

User asks: "migrate all my AI Build Lab automations from launchd to n8n"

1. Scan `~/Library/LaunchAgents/com.aibuildlab.*.plist`
2. Parse each one
3. For each:
   - **morning-brief.plist** (calendar interval daily 02:00, runs python script with GRAND_CENTRAL_API_KEY env var) → propose Schedule Trigger + Execute Command, flag the env var as a secret to move into n8n credential
   - **fleet-health.plist** (StartInterval 900 = every 15 min, runs bash script) → propose Schedule Trigger `*/15 * * * *` + Execute Command (or rebuild script logic as native nodes)
   - **slack-mention-listener.plist** (KeepAlive: true) → SKIP, this is a daemon, not a scheduled job
4. Build workflow JSONs
5. Show summary table, get approval
6. Bulk import as inactive workflows
7. Walk user through verification + decommission flow
