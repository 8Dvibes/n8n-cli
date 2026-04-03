"""Source control operations for n8n-cli."""

import json
from typing import Optional

from .client import N8nClient


def pull(client: N8nClient, force: bool = False, as_json: bool = False) -> None:
    """Pull from source control."""
    body = {}
    if force:
        body["force"] = True

    result = client.post("/source-control/pull", body=body if body else None)

    if as_json:
        print(json.dumps(result, indent=2))
        return

    if isinstance(result, dict):
        status = result.get("statusCode", "done")
        print(f"Pull completed: {status}")
        variables = result.get("variables", [])
        workflows = result.get("workflows", [])
        credentials = result.get("credentials", [])
        if variables:
            print(f"  Variables: {len(variables)}")
        if workflows:
            print(f"  Workflows: {len(workflows)}")
        if credentials:
            print(f"  Credentials: {len(credentials)}")
    else:
        print("Pull completed.")
