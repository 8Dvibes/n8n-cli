---
name: n8n-webhook-test
description: "Send test payloads to n8n webhook workflows from the terminal. Use when testing webhooks, debugging webhook integrations, or verifying workflow triggers."
user_invocable: true
---

# /n8n-webhook-test — Test Webhook Workflows

Fire test requests at webhook-triggered workflows.

## Arguments

- `/n8n-webhook-test <workflow-id>` — Send empty POST to the workflow's webhook
- `/n8n-webhook-test <workflow-id> --data '{"key": "value"}'` — Send specific payload
- `/n8n-webhook-test list` — List all webhook URLs from active workflows

## Procedure

### List Available Webhooks

```bash
n8n-cli webhooks list
```

Shows all webhook endpoints from active workflows with their methods and paths.

### Test a Specific Webhook

```bash
# Auto-discovers the webhook path from the workflow, sends a test request
n8n-cli webhooks test <workflow-id> --data '{"test": true, "message": "Hello from CLI"}'
```

The command:
1. Fetches the workflow to find the webhook node
2. Extracts the webhook path and HTTP method
3. Sends the request to the test webhook URL
4. Shows the response

### Important Notes

- **Test URL vs Production URL**: The CLI uses the test webhook URL (`/webhook-test/...`).
  The workflow must have "Listen for test event" active in the n8n UI, OR be active
  (production webhooks at `/webhook/...` work when the workflow is active).

- **For production webhooks**: The workflow must be activated first:
  ```bash
  n8n-cli workflows activate <id>
  ```

- **Custom payloads**: Match the data format your workflow expects. Check the webhook
  node's configuration for expected fields.

## Output

```
Workflow:  My Webhook Flow (abc123)
Webhook:   Webhook Trigger
Path:      my-custom-path
Method:    POST
URL:       https://aibuildlab.app.n8n.cloud/webhook-test/my-custom-path
Sending test request...

Status: 200
Response:
{
  "success": true,
  "message": "Processed"
}
```
