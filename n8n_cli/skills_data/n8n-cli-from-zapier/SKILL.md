---
name: n8n-cli-from-zapier
description: "Migrate a Zapier zap to an equivalent n8n workflow. Reads a zap export (JSON or screenshot description) and generates the n8n workflow JSON. Use when moving off Zapier to n8n for cost, ownership, or flexibility reasons."
user_invocable: true
---

# /n8n-cli-from-zapier — Zapier → n8n Migration

Convert a Zapier zap to an equivalent n8n workflow. Supports JSON exports, manual descriptions, and step-by-step rebuilds.

## Procedure

1. **Get the zap**:
   - **Best**: user provides a Zapier zap JSON export (Zapier supports this for some plans)
   - **Good**: user provides screenshots of the zap and a description of each step
   - **OK**: user describes the zap in plain English ("when a new row is added to Google Sheets, post to Slack and create a Notion page")

2. **Parse the zap structure**:
   - **Trigger**: identify the trigger app and event (Gmail new email, Sheets new row, Webhook, Schedule, etc.)
   - **Steps**: each action with its app, action type, and field mappings
   - **Filters / Paths**: Zapier's branching logic
   - **Formatter / Code steps**: data transformations

3. **Map Zapier apps to n8n nodes**:
   - Most major apps have direct n8n equivalents (Slack, Gmail, Notion, Sheets, Airtable, HubSpot, Stripe, Trello, etc.)
   - For apps with no n8n node, use HTTP Request node + the app's REST API
   - For Formatter steps, use Set or Code nodes
   - For Paths (Zapier's branching), use IF or Switch nodes
   - For Filter steps, use IF nodes
   - For Schedule, use Schedule Trigger
   - For Webhook by Zapier, use Webhook Trigger

4. **Map field references**:
   - Zapier uses `{{trigger.field_name}}` style references
   - n8n uses `{{$json.field_name}}` or `{{$('Node Name').item.json.field}}`
   - Translate each field reference

5. **Build the n8n workflow JSON**:
   - Start with the trigger
   - Chain the mapped nodes in order
   - Wire field references between steps
   - Add credentials (point at existing instance creds; the user will need to verify or create them)

6. **Show the proposed workflow**:
   - Side-by-side: "Zapier zap had 6 steps, n8n workflow has 6 nodes"
   - Highlight any approximations: "Zapier's Filter step → n8n IF node — slightly different operators, verify the logic"
   - Highlight any creds the user will need to set up

7. **Import** (with approval):
   - `n8n-cli wf import` (don't activate)
   - Walk the user through testing it side-by-side with the original Zapier zap
   - Once verified, the user can pause the Zapier zap and activate the n8n workflow

## Output format

- Source zap structure (numbered steps)
- Mapped n8n structure (numbered nodes, side-by-side)
- Credentials needed (with creation instructions if any are missing)
- Test plan: how to verify side-by-side
- Cutover plan: how to switch from Zapier to n8n safely

## Tips

- **Cost framing**: Zapier charges per task. n8n on cloud is also priced per execution but typically much cheaper per task. For self-hosted, it's free per task. Mention the projected savings if relevant.
- **Reliability framing**: n8n gives you full control of error handling. Zapier's retries are opaque. Highlight this when migrating mission-critical zaps.
- **Cutover safety**: never delete the Zapier zap immediately. Pause it, run the n8n version in parallel for a week, then delete.
- For zaps with **lots of branches** (Zapier Paths), the conversion can be tricky. n8n's branching is powerful but the mental model is different. Walk through it step by step.
- For zaps that depend on **Zapier-specific features** (Built-in Apps like Schedule, Filter, Formatter), the n8n equivalents are usually cleaner.
- For zaps that hit **niche apps n8n doesn't support natively**, the HTTP Request node + the app's API is the bridge. Always works, just takes more setup.

## Marketing-friendly framing

This is one of the most-requested migrations in the n8n community. If the user is migrating multiple zaps, suggest doing the easiest one first to build confidence, then tackling the hardest one with the most external value.
