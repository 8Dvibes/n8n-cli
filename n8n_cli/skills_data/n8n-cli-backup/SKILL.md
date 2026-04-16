---
name: n8n-backup
description: "Back up an entire n8n instance to a git-tracked directory. Exports all workflows, credentials, tags, and variables as a snapshot. NOT single-file export -- use /n8n-export for that. Use when creating full instance snapshots."
user_invocable: true
---

# /n8n-backup — Full Instance Backup

Export everything from an n8n instance to a structured, git-friendly directory.

## Arguments

- `/n8n-backup` — Backup default profile (cloud)
- `/n8n-backup --profile hostinger` — Backup specific instance
- `/n8n-backup --all` — Backup all configured profiles

## Procedure

### Step 1: Create Backup Directory

```bash
BACKUP_DIR=~/GitHub/n8n-backups/$(date +%Y-%m-%d)/<profile-name>
mkdir -p "$BACKUP_DIR/workflows" "$BACKUP_DIR/meta"
```

### Step 2: Export All Workflows

```bash
n8n-cli --profile <name> --json workflows list > "$BACKUP_DIR/meta/workflows.json"

# Export each workflow individually (clean filenames)
for each workflow in the list:
    n8n-cli --profile <name> workflows export <id> -o "$BACKUP_DIR/workflows/<safe-name>_<id>.json"
```

### Step 3: Export Metadata

```bash
# Credentials (IDs and types only, no secrets)
n8n-cli --profile <name> --json credentials list > "$BACKUP_DIR/meta/credentials.json"

# Tags
n8n-cli --profile <name> --json tags list > "$BACKUP_DIR/meta/tags.json"

# Variables
n8n-cli --profile <name> --json variables list > "$BACKUP_DIR/meta/variables.json"

# Users
n8n-cli --profile <name> --json users list > "$BACKUP_DIR/meta/users.json"
```

### Step 4: Write Manifest

Create a `manifest.json` with:
- Backup timestamp
- Profile name and API URL
- Workflow count
- Credential count
- n8n version (if available from health check)

### Step 5: Git Commit (if in a git repo)

```bash
cd ~/GitHub/n8n-backups
git add -A
git commit -m "n8n backup: <profile> — <N> workflows, <timestamp>"
```

## Output

```
Backup complete: <profile>
  Workflows: N exported
  Credentials: N listed
  Tags: N listed
  Variables: N listed
  Location: ~/GitHub/n8n-backups/2026-04-03/cloud/
```

## Scheduling

This skill works well with `/schedule` for automated nightly backups:
```
/schedule "n8n-backup --all" --cron "0 2 * * *"
```
