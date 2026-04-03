# n8n-cli Example Prompts

Copy-paste these into Claude Code (or any AI agent) to see n8n-cli in action. Each one is a real workflow you'd actually use.

## Getting Started

> "Set up n8n-cli with my instance at https://my-n8n.example.com/api/v1 with API key xyz, then run a health check and show me all my active workflows."

## Debug Failed Workflows

> "Check my n8n instance for any failed executions in the last 24 hours. For each failure, tell me which workflow failed, what node caused it, and what the error was. Suggest a fix for each one."

## Export All Workflows to Git

> "Export every active workflow from my n8n instance to a folder called n8n-workflows/. Use clean filenames based on the workflow name. Then list what you exported."

## Find the Right Node

> "I need to send data to Google Sheets from a webhook. Search the n8n node catalog for Google Sheets nodes, show me what operations are available, and what credentials I'll need."

## Build a Workflow from Scratch

> "Build me an n8n workflow that triggers on a schedule every morning at 8am, checks for new rows in a Google Sheet, and posts a summary to Slack. Look up the correct node schemas before building the JSON, then import it to my n8n instance."

## Credential Audit

> "List all the credentials on my n8n instance. Then check which ones aren't being used by any active workflow. Those are cleanup candidates."

## Compare Two Instances

> "I have two n8n profiles set up: cloud and selfhosted. List the workflows on both instances and tell me which ones exist on cloud but not on selfhosted."

## Monitor for Errors

> "Check my n8n instance for errors every 5 minutes. If you find any new failures, tell me what broke and suggest a fix."

## Explore AI Nodes

> "Show me all the n8n nodes that can be used as AI agent tools. For the top 5 most interesting ones, show me their full property schemas."

## Webhook Discovery

> "List all the webhook endpoints across my active workflows. For each one, show me the HTTP method and path."

## Security Audit

> "Run a security audit on my n8n instance. Show me any credentials that aren't being used, any risky nodes, and any unprotected webhooks."

## Multi-Instance Management

> "Run a health check on both my cloud and selfhosted n8n instances. Then compare the active workflow counts and show me which instance has more."

## Quick Daily Check

> "Give me a quick status report on my n8n instance. How many active workflows, any errors today, and how many executions ran successfully."

---

## Tips

- These prompts work with Claude Code, Cursor CLI, Codex, Gemini CLI, or any agent that can run Bash
- The agent will use `n8n-cli` commands under the hood -- you don't need to know the commands yourself
- Add `--json` to any command if you want the agent to process structured data
- Use `--profile <name>` to target different n8n instances

---

Built by [AI Build Lab](https://aibuildlab.com) | [GitHub](https://github.com/8Dvibes/n8n-cli) | [@tyfisk](https://x.com/tyfisk)
