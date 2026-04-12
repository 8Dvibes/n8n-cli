---
name: n8n-create
description: "Describe a workflow in English, Claude builds the JSON, and imports it to n8n via n8n-cli. Use when building new n8n workflows from a description."
user_invocable: true
---

# /n8n-create — Build n8n Workflow from Description

Translate a natural language workflow description into n8n workflow JSON and import it.

## Arguments

`/n8n-create <description of what the workflow should do>`

## Procedure

### Step 1: Understand Requirements

Ask clarifying questions if the description is ambiguous:
- What triggers the workflow? (webhook, schedule, manual, event)
- What services are involved? (Slack, Gmail, HTTP APIs, databases)
- What's the expected output? (message, email, database write, API call)
- Any error handling needed?

### Step 2: Look Up Nodes and Credentials

```bash
# Find the right nodes for each service mentioned
n8n-cli --json nodes search <service-name>

# Get full property schema for each node you'll use
n8n-cli --json nodes get <node-name> --full

# Check what credentials are available on the instance
n8n-cli credentials list --json
```

Match required services to available credentials. Flag any missing credentials.

### Step 3: Build Workflow JSON

Use the full node schemas from Step 2 to construct accurate JSON. Do NOT guess at property names or structures.

Build with:
- Proper node types using full prefix: `n8n-nodes-base.{nodeName}`
- For AI/langchain nodes: `@n8n/n8n-nodes-langchain.{nodeName}`
- Correct connections array linking nodes
- Proper node positions (spread nodes ~250px apart horizontally)
- Credential references matching available credential IDs
- Property names and values matching the actual node schema

**Critical n8n JSON patterns:**
- IF node conditions MUST include `options.version: 2`
- Execute Workflow nodes MUST use resource locator format: `{__rl: true, value: "ID", mode: "id"}`
- Webhook paths should be lowercase, hyphenated
- Node names must be unique within the workflow

### Step 4: Save and Import

```bash
# Save the workflow JSON
cat > /tmp/n8n-workflow-create.json << 'WORKFLOW_EOF'
{workflow json here}
WORKFLOW_EOF

# Import to n8n
n8n-cli workflows import /tmp/n8n-workflow-create.json

# Optionally activate
n8n-cli workflows activate <returned-id>
```

### Step 5: Verify

```bash
n8n-cli --json workflows get <id>
```

## Output

Tell the user:
1. What was created (workflow name, node count)
2. The workflow ID
3. Whether it's active or inactive
4. Any credential gaps that need manual setup in the n8n UI
5. Link format: `https://aibuildlab.app.n8n.cloud/workflow/<id>`

## Tips

- Start simple. Build the core flow first, add error handling after.
- Always include a Manual Trigger node alongside the primary trigger for testing.
- Use Set nodes to transform data between services rather than complex expressions.
- For multi-step workflows, consider sub-workflows for reusability.
