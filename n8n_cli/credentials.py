"""Credential operations for n8n-cli."""

import json
from typing import Optional

from .client import N8nClient
from .exceptions import N8nValidationError


def list_credentials(
    client: N8nClient,
    cred_type: Optional[str] = None,
    limit: Optional[int] = None,
    as_json: bool = False,
) -> None:
    """List credentials with optional type filter."""
    params = {}
    if cred_type:
        params["type"] = cred_type

    if limit:
        creds = client.paginate("/credentials", params=params, limit=limit)
    else:
        creds = client.paginate("/credentials", params=params)

    if as_json:
        print(json.dumps(creds, indent=2))
        return

    if not creds:
        print("No credentials found.")
        return

    print(f"{'ID':<20} {'Type':<30} {'Name'}")
    print("-" * 75)
    for c in creds:
        cid = c.get("id", "")
        name = c.get("name", "untitled")
        ctype = c.get("type", "unknown")
        print(f"{cid:<20} {ctype:<30} {name}")
    print(f"\nTotal: {len(creds)} credential(s)")


def get_credential(client: N8nClient, credential_id: str, as_json: bool = False) -> None:
    """Get a single credential by ID (no secrets returned by API).

    Note: Some n8n instances (especially cloud) may not support this endpoint.
    Falls back to filtering the list endpoint.
    """
    from .client import N8nApiError
    try:
        cred = client.get(f"/credentials/{credential_id}")
    except N8nApiError as e:
        if e.status == 405:
            # Cloud instances don't support GET /credentials/{id}
            # Fall back to listing all and filtering
            all_creds = client.paginate("/credentials")
            cred = None
            for c in all_creds:
                if c.get("id") == credential_id:
                    cred = c
                    break
            if not cred:
                raise N8nValidationError(f"Credential '{credential_id}' not found.")
        else:
            raise

    if as_json:
        print(json.dumps(cred, indent=2))
        return

    print(f"ID:       {cred.get('id')}")
    print(f"Name:     {cred.get('name')}")
    print(f"Type:     {cred.get('type')}")
    print(f"Created:  {cred.get('createdAt', 'N/A')}")
    print(f"Updated:  {cred.get('updatedAt', 'N/A')}")


def get_credential_schema(client: N8nClient, type_name: str, as_json: bool = False) -> None:
    """Get the schema for a credential type."""
    schema = client.get(f"/credentials/schema/{type_name}")

    if as_json:
        print(json.dumps(schema, indent=2))
        return

    if isinstance(schema, list):
        for prop in schema:
            name = prop.get("displayName", prop.get("name", ""))
            required = " (required)" if prop.get("required") else ""
            ptype = prop.get("type", "")
            print(f"  {name}: {ptype}{required}")
    else:
        print(json.dumps(schema, indent=2))


def create_credential(client: N8nClient, file_path: str, as_json: bool = False) -> None:
    """Create a credential from a JSON file."""
    with open(file_path) as f:
        data = json.load(f)

    result = client.post("/credentials", body=data)

    if as_json:
        print(json.dumps(result, indent=2))
        return

    print(f"Created credential: {result.get('id')} - {result.get('name')}")


def delete_credential(client: N8nClient, credential_id: str, as_json: bool = False) -> None:
    """Delete a credential."""
    result = client.delete(f"/credentials/{credential_id}")

    if as_json:
        print(json.dumps(result, indent=2) if result else '{"deleted": true}')
        return

    print(f"Deleted credential: {credential_id}")


def transfer_credential(client: N8nClient, credential_id: str, project_id: str, as_json: bool = False) -> None:
    """Transfer a credential to another project."""
    result = client.put(f"/credentials/{credential_id}/transfer", body={"destinationProjectId": project_id})
    if as_json:
        print(json.dumps(result, indent=2) if result else '{"transferred": true}')
        return
    print(f"Transferred credential {credential_id} to project {project_id}")
