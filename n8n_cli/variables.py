"""Variable operations for n8n-cli."""

import json
from typing import Optional

from .client import N8nClient
from .exceptions import N8nValidationError


def list_variables(client: N8nClient, limit: Optional[int] = None, as_json: bool = False) -> None:
    """List all variables."""
    if limit is not None:
        variables = client.paginate("/variables", limit=limit)
    else:
        variables = client.paginate("/variables")

    if as_json:
        print(json.dumps(variables, indent=2))
        return

    if not variables:
        print("No variables found.")
        return

    print(f"{'ID':<12} {'Key':<30} {'Value'}")
    print("-" * 65)
    for v in variables:
        print(f"{v.get('id', ''):<12} {v.get('key', ''):<30} {v.get('value', '')}")
    print(f"\nTotal: {len(variables)} variable(s)")


def create_variable(client: N8nClient, key: str, value: str, as_json: bool = False) -> None:
    """Create a variable."""
    result = client.post("/variables", body={"key": key, "value": value})
    if as_json:
        print(json.dumps(result, indent=2))
        return
    print(f"Created variable: {result.get('id')} - {key}={value}")


def get_variable(client: N8nClient, variable_id: str, as_json: bool = False) -> None:
    """Get a variable by ID."""
    var = client.get(f"/variables/{variable_id}")
    if as_json:
        print(json.dumps(var, indent=2))
        return
    print(f"ID:    {var.get('id')}")
    print(f"Key:   {var.get('key')}")
    print(f"Value: {var.get('value')}")


def update_variable(client: N8nClient, variable_id: str, key: Optional[str] = None, value: Optional[str] = None, as_json: bool = False) -> None:
    """Update a variable. Requires at least --key or --value."""
    body = {}
    if key is not None:
        body["key"] = key
    if value is not None:
        body["value"] = value
    if not body:
        raise N8nValidationError("variables update requires --key or --value (or both).")
    result = client.put(f"/variables/{variable_id}", body=body)
    if as_json:
        print(json.dumps(result, indent=2))
        return
    print(f"Updated variable: {variable_id}")


def delete_variable(client: N8nClient, variable_id: str, as_json: bool = False) -> None:
    """Delete a variable."""
    result = client.delete(f"/variables/{variable_id}")
    if as_json:
        print(json.dumps(result, indent=2) if result else '{"deleted": true}')
        return
    print(f"Deleted variable: {variable_id}")
