"""Webhook operations for n8n-cli."""

import json
import ssl
import urllib.error
import urllib.request
from typing import Optional

from .client import N8nClient
from .exceptions import N8nConnectionError, N8nValidationError


def _webhook_base_url(api_url: str) -> str:
    """Derive the webhook base URL from the API URL.

    Strips the /api/v1 suffix to get the instance base URL, which is
    used to construct webhook and webhook-test URLs.
    """
    if api_url.endswith("/api/v1"):
        return api_url[:-7]
    elif api_url.endswith("/api/v1/"):
        return api_url[:-8]
    idx = api_url.find("/api/")
    return api_url[:idx] if idx != -1 else api_url


def test_webhook(
    client: N8nClient,
    workflow_id: str,
    data: Optional[str] = None,
    method: str = "POST",
    as_json: bool = False,
) -> None:
    """Send a test payload to a webhook workflow.

    Looks up the workflow to find its webhook path, then sends a request.
    """
    # First, get the workflow to find the webhook node
    wf = client.get(f"/workflows/{workflow_id}")
    nodes = wf.get("nodes", [])

    webhook_node = None
    for node in nodes:
        node_type = node.get("type", "")
        if "webhook" in node_type.lower():
            webhook_node = node
            break

    if not webhook_node:
        raise N8nValidationError(f"No webhook node found in workflow {workflow_id}.")

    # Extract webhook path from node parameters
    params = webhook_node.get("parameters", {})
    path = params.get("path", "")
    node_method = params.get("httpMethod", "POST")

    if not path:
        raise N8nValidationError("Webhook node found but no path configured.")

    # Use the node's configured method unless user explicitly overrides
    if method == "POST" and node_method != "POST":
        method = node_method

    # Build the webhook URL using the shared helper
    base = _webhook_base_url(client.api_url)
    webhook_url = f"{base}/webhook-test/{path}"

    # Parse the data payload
    payload = None
    if data:
        try:
            payload = json.loads(data)
        except json.JSONDecodeError as e:
            raise N8nValidationError(f"Invalid JSON data: {data}") from e

    if not as_json:
        print(f"Workflow:  {wf.get('name')} ({workflow_id})")
        print(f"Webhook:   {webhook_node.get('name')}")
        print(f"Path:      {path}")
        print(f"Method:    {method}")
        print(f"URL:       {webhook_url}")
        print(f"Sending test request...")
        print()

    # Send the webhook request
    req_data = json.dumps(payload).encode("utf-8") if payload else None
    headers = {"Content-Type": "application/json"} if payload else {}

    req = urllib.request.Request(
        webhook_url,
        data=req_data,
        headers=headers,
        method=method.upper(),
    )

    try:
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            status = resp.status

            if as_json:
                try:
                    result = json.loads(body)
                    print(json.dumps({"status": status, "response": result}, indent=2))
                except json.JSONDecodeError:
                    print(json.dumps({"status": status, "response": body}, indent=2))
            else:
                print(f"Status: {status}")
                try:
                    result = json.loads(body)
                    print(f"Response:\n{json.dumps(result, indent=2)}")
                except json.JSONDecodeError:
                    print(f"Response:\n{body}")

    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        if as_json:
            print(json.dumps({"status": e.code, "error": body}, indent=2))
        else:
            print(f"Status: {e.code}")
            print(f"Error: {body}")
        raise N8nConnectionError(f"Webhook request failed with HTTP {e.code}") from e
    except urllib.error.URLError as e:
        raise N8nConnectionError(
            f"{e.reason}. "
            "The workflow must be active for production webhooks, "
            "or have 'Listen for test event' running for test webhooks."
        ) from e


def list_webhooks(client: N8nClient, as_json: bool = False) -> None:
    """List all webhook URLs across active workflows."""
    workflows = client.paginate("/workflows", params={"active": "true"})

    webhooks = []
    for wf in workflows:
        nodes = wf.get("nodes", [])
        for node in nodes:
            node_type = node.get("type", "")
            if "webhook" in node_type.lower() and "respond" not in node_type.lower():
                params = node.get("parameters", {})
                path = params.get("path", "")
                method = params.get("httpMethod", "POST")
                base = _webhook_base_url(client.api_url)
                if path:
                    webhooks.append({
                        "workflow_id": wf.get("id"),
                        "workflow_name": wf.get("name"),
                        "node_name": node.get("name"),
                        "path": path,
                        "method": method,
                        "url": f"{base}/webhook/{path}",
                        "test_url": f"{base}/webhook-test/{path}",
                    })

    if as_json:
        print(json.dumps(webhooks, indent=2))
        return

    if not webhooks:
        print("No webhook endpoints found in active workflows.")
        return

    print(f"{'Method':<8} {'Path':<30} {'Workflow'}")
    print("-" * 75)
    for wh in webhooks:
        print(f"{wh['method']:<8} {wh['path']:<30} {wh['workflow_name']}")
    print(f"\nTotal: {len(webhooks)} webhook(s)")
