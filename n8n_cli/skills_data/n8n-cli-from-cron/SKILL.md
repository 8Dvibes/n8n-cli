---
name: n8n-cli-from-cron
description: "Convert crontab entries into equivalent n8n workflows. Reads cron jobs and generates one workflow per entry. Use when migrating off bare cron onto n8n for visibility and error handling."
user_invocable: true
---

# /n8n-cli-from-cron — Crontab → n8n Workflows

Take a crontab (or a list of cron-style scheduled tasks) and generate one n8n workflow per entry.

## Procedure

1. **Get the source**:
   - User pastes their crontab content
   - Or user provides a path: `cat /etc/crontab` or `crontab -l`
   - Parse each line into: schedule (cron expression), command, optional comment

2. **For each cron entry**:
   - **Detect the command type**:
     - Shell command (`bash /path/to/script.sh`)
     - Python script (`python3 /path/to/foo.py`)
     - Node script
     - HTTP call (`curl https://...`)
     - Database query (`mysql -e "..."`)
     - Backup job (`rsync`, `tar`, etc.)
   - **Extract intent**: read the comment if present. Otherwise, ask the user what the job does.

3. **Map to n8n nodes**:
   - Schedule trigger with the same cron expression
   - For shell commands → Execute Command node (if self-hosted with shell access) OR rebuild the command's logic in native n8n nodes
   - For curl → HTTP Request node
   - For Python/Node scripts → Code node (paste the script body) OR if it's reasonable, rebuild as native nodes
   - For DB queries → MySQL/Postgres/etc. node with credential
   - For backups → Read/Write Files + S3/SFTP node
   - For email reports → Send Email node

4. **Add observability** that bare cron didn't have:
   - Error handler branch on every external call
   - Slack/email alert node on failure (suggest a default alert channel)
   - Optional: log the run to a database or file for audit

5. **Generate one workflow per cron entry** (or grouped if the user prefers fewer workflows):
   - Save each as JSON
   - Show the user the proposed workflow names and what they'll do
   - Confirm before importing

6. **Bulk import** (only after approval):
   - `n8n-cli wf import` for each
   - DO NOT activate by default — let the user verify each one in the UI first
   - Print a summary: "Imported 12 workflows. Activate them when ready: `n8n-cli wf activate <id>`"

7. **Suggest decommissioning the old cron entries**:
   - Don't delete from crontab automatically
   - Print a checklist: "Once you've verified each n8n workflow runs correctly, comment out the corresponding cron entry. Don't delete until you've seen the n8n version run successfully at least 3 times."

## Output format

- Show the parsed crontab as a numbered list
- For each entry, show: original cron, original command, proposed n8n node graph, name
- Walk through approval one entry at a time for tricky cases
- For trivial entries (single curl, single script call), batch-confirm

## Tips

- The biggest win of moving cron → n8n is visibility. Every run shows up in the n8n execution history with status, duration, output. No more silent cron failures.
- Some cron entries are too complex to be worth migrating (multi-stage shell pipelines, etc.). For those, suggest leaving them in cron and having n8n monitor them via a heartbeat workflow.
- Time zones: cron usually runs in the host's local time, n8n in the instance's configured time. Confirm and adjust the cron expressions if needed.
- For shell scripts that read environment variables, the n8n equivalent reads from credentials or n8n variables. Walk through each env var the script uses.
- This pairs with /n8n-cli-meta-monitor — once your jobs are in n8n, you also get failure alerting for free.
