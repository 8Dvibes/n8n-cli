---
name: n8n-cli-template
description: "Templatize or instantiate n8n workflows. Strips IDs and credentials to create reusable templates, or fills placeholders to create new workflows from templates. Use for sharing patterns across instances or building a library."
user_invocable: true
---

# /n8n-cli-template — Workflow Templating

Two modes: **extract** a template from an existing workflow, or **instantiate** a new workflow from a template.

## Mode 1: Extract template from a workflow

### Procedure

1. **Get the workflow**:
   - `n8n-cli wf export <id> -o /tmp/source.json`

2. **Strip non-portable fields**:
   - `id` (will be assigned on import)
   - `versionId`, `createdAt`, `updatedAt`, `homeProject`, `sharedWithProjects`
   - `webhookId` on every webhook node (n8n regenerates on import)
   - `credentials.<name>.id` references (replace with `{{CREDENTIAL_<name>}}` placeholders)
   - Hard-coded URLs in HTTP Request nodes (offer to parameterize as `{{API_URL}}`)
   - Hard-coded channel IDs / user IDs / project IDs (offer to parameterize)

3. **Add a template manifest** at the top of the JSON as `_template`:
   ```json
   {
     "_template": {
       "name": "Slack Daily Digest",
       "version": "1.0.0",
       "description": "Posts a daily summary of N items to a Slack channel",
       "placeholders": [
         {"key": "CREDENTIAL_slack", "type": "credential", "credential_type": "slackOAuth2Api", "description": "Slack workspace OAuth"},
         {"key": "CHANNEL_ID", "type": "string", "description": "Slack channel ID to post to"},
         {"key": "SCHEDULE_CRON", "type": "cron", "description": "When to post", "default": "0 9 * * *"}
       ]
     },
     ...rest of workflow
   }
   ```

4. **Save the template**:
   - Default location: `~/n8n-templates/<slug>.json`
   - Or user-specified path
   - Print a usage example: invoke this skill again as `/n8n-cli-template` from inside Claude Code and pass the template path when prompted

## Mode 2: Instantiate a workflow from a template

### Procedure

1. **Read the template file**
2. **Parse `_template.placeholders`** — for each one, prompt the user to fill in
3. **For credential placeholders**:
   - List existing credentials of the matching type: `n8n-cli --json creds list --type <type>`
   - Let the user pick from the list, or create a new one
4. **Substitute placeholders** throughout the JSON
5. **Strip the `_template` block** before import
6. **Import**:
   - `n8n-cli wf import /tmp/instantiated.json` (don't activate by default)
   - Report the new workflow ID and a link to view it in the n8n UI

## Output format

For **extract**: confirm what was stripped, show the placeholder list, save to disk, print next-step instructions.

For **instantiate**: walk the user through each placeholder interactively, show a summary of substitutions, confirm before importing.

## Tips

- Templates should be portable across cloud and self-hosted. Don't hardcode project IDs.
- For templates that ship with multiple workflows (parent + children), package as a directory of JSONs with a shared manifest.
- If the user has a Notion or Slack message describing the workflow they want to template, read it for context to write the template description.
- When instantiating, always preview the substituted JSON before importing — easier to catch a typo before it lands as a workflow.
- Templates with 0 placeholders are basically just clones — that's fine, but mention it.

## Future hook

Eventually `n8n-cli` could ship a built-in template library (`n8n-cli templates list`, `n8n-cli templates install <name>`) — this skill is the human-friendly front end for that future surface.
