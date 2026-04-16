---
name: n8n-cli-from-mcp
description: "Convert an MCP server or Claude Code skill into an n8n workflow. Moves agent capabilities into n8n to run on a schedule or webhook without an agent. Use when productizing an MCP-driven prototype."
user_invocable: true
---

# /n8n-cli-from-mcp — MCP / Skill → n8n Workflow

Take an MCP server config or a Claude Code skill and generate an n8n workflow that does the same thing without needing an agent at runtime.

## Procedure

1. **Identify the source**:
   - **MCP server**: ask for the server name, command, and tools it exposes (or read from `~/.config/claude/mcp.json` style config)
   - **Claude Code skill**: ask for the skill name or path to its SKILL.md

2. **Read the source's actual capabilities**:
   - For an MCP server: list the tools, their input schemas, what they return
   - For a skill: read the procedure section, identify what commands/APIs it calls

3. **Map MCP tools / skill steps to n8n nodes**:
   - HTTP API call → HTTP Request node
   - Slack post → Slack node
   - Notion read/write → Notion node
   - File read/write → Read/Write Files node
   - Code execution → Code node (JS or Python)
   - LLM call → OpenAI / Anthropic node
   - Branching logic → IF / Switch node

4. **Identify what the workflow's trigger should be**:
   - If the original MCP/skill was invoked by an agent on demand → Manual Trigger or Webhook
   - If it was meant to run on a schedule → Schedule Trigger
   - If it was reactive to events → Webhook Trigger or specific event trigger node

5. **Build the workflow JSON**:
   - Start with the trigger
   - Chain the mapped nodes
   - Add credentials where needed (use existing instance credentials, not new ones)
   - Add error handling for any external API calls

6. **Show the proposed workflow** before importing:
   - Print the node-by-node plan
   - Highlight any places where the mapping is approximate ("MCP tool X has no direct n8n equivalent — using Code node with the same logic")

7. **Import** (only after user approval):
   - `n8n-cli wf import /tmp/from-mcp.json` (don't activate)
   - Walk the user through testing it manually first
   - Then activate

## Output format

- Show the source's tools/steps as a numbered list
- Show the mapped n8n nodes as a parallel numbered list
- Highlight any mappings that need user judgment
- Confirm before importing

## Tips

- The most natural conversions are MCP servers that just call HTTP APIs or run scripts — those map 1:1 to HTTP Request or Code nodes.
- MCP servers with deep state (like memory MCPs) don't map well — n8n is stateless between runs unless you wire up a database. Surface this limitation up front.
- Some Claude Code skills are pure prompts (e.g. "summarize this") — those need an LLM node in the n8n workflow, which means a credential and per-run cost.
- For complex MCPs (browser automation, etc.), suggest keeping them as MCPs and having n8n call out to them via HTTP if exposed, rather than rebuilding them.
- Document the resulting n8n workflow with /n8n-cli-document so the team can maintain it without referring back to the original MCP.
