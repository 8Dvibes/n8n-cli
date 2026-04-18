---
name: n8n-cli-to-mcp
description: "Expose an n8n workflow as an MCP tool for AI agents. Generates a tool definition that Claude, Cursor, or Codex can call. Inverse of /n8n-cli-from-mcp. Use when agents need to invoke an n8n workflow on demand."
user_invocable: true
---

# /n8n-cli-to-mcp — n8n Workflow → Agent Tool

Take an n8n workflow (typically webhook-triggered) and produce a tool definition that any AI agent can call.

## Procedure

1. **Get the workflow**:
   - `n8n-cli --json wf get <id>`
   - Confirm it's webhook-triggered (other trigger types can't be called by an agent on demand)

2. **Infer the tool's interface**:
   - **Name**: derive from the workflow name, slugified
   - **Description**: derive from the workflow's purpose. If unclear, ask the user for a one-line description.
   - **Input schema**: walk the nodes downstream from the webhook trigger and find what fields are referenced from `$json.foo`. Build a JSON schema.
   - **Output shape**: look at the final node — does it return JSON? If so, infer the response schema from a recent successful execution (`exec list --workflow-id <id> --status success --limit 1` then `exec get <id>`).

3. **Output format options** (ask the user which they want):

   a. **MCP tool definition** (for Claude Code MCP servers):
   ```json
   {
     "name": "n8n_process_order",
     "description": "Submits an order to the order processing workflow",
     "inputSchema": {
       "type": "object",
       "properties": {
         "customer_id": {"type": "string"},
         "product_id": {"type": "string"},
         "quantity": {"type": "integer"}
       },
       "required": ["customer_id", "product_id", "quantity"]
     }
   }
   ```

   Plus a wrapper script that bridges the MCP call to the n8n webhook URL.

   b. **OpenAI function-calling spec**:
   ```json
   {
     "type": "function",
     "function": {
       "name": "n8n_process_order",
       "description": "...",
       "parameters": { /* same schema */ }
     }
   }
   ```

   c. **Anthropic tool spec**:
   ```json
   {
     "name": "n8n_process_order",
     "description": "...",
     "input_schema": { /* same schema */ }
   }
   ```

   d. **Simple HTTP tool** (for any agent):
   - Endpoint URL
   - Method (POST)
   - Auth header / API key
   - Request body schema
   - Response schema
   - Example curl

4. **Generate a wrapper** if needed:
   - For MCP: a small Python script that registers as an MCP server and proxies calls to the n8n webhook
   - For HTTP: just the spec (the agent calls the webhook directly)

5. **Save the spec** to:
   - `~/.claude/tools/n8n-<workflow-slug>.json` (for Claude Code MCP integration)
   - Or wherever the user wants

## Output format

- Show the inferred input/output schemas
- Show the chosen tool spec
- Print integration instructions (how to register the tool with the user's agent of choice)

## Tips

- The webhook URL needs to be reachable from wherever the agent runs. For local Claude Code → cloud n8n, that's fine. For local Claude → self-hosted n8n on a private network, use Tailscale or expose via tunnel.
- Always include an API key on the n8n webhook (use header auth) so agents can't be tricked into hitting it from arbitrary contexts.
- For workflows with long execution times (>30s), wrap as an async tool: agent kicks off the workflow, n8n returns an execution ID, agent polls `exec get <id>` until done.
- Surface the workflow's failure modes (from /n8n-cli-document output) in the tool description so the agent knows when to retry vs give up.
- This is the *inverse* of /n8n-cli-from-mcp — together they let you move logic between agent-runtime and n8n-runtime as needed.

## Example end-to-end

User says: "I built an n8n workflow that takes a customer ID and returns their LTV. Wrap it as a tool I can call from Claude Code."

1. Find the workflow → `n8n-cli --json wf list --name "LTV"`
2. Get its webhook URL → check the trigger node config
3. Inspect input/output → walk nodes
4. Generate MCP tool spec
5. Save to `~/.claude/tools/n8n-customer-ltv.json`
6. Tell user how to register the tool with Claude Code
