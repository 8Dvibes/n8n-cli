"""Tag operations for n8n-cli."""

import json
from typing import Optional

from .client import N8nClient


def list_tags(client: N8nClient, limit: Optional[int] = None, as_json: bool = False) -> None:
    """List all tags."""
    if limit is not None:
        tags = client.paginate("/tags", limit=limit)
    else:
        tags = client.paginate("/tags")

    if as_json:
        print(json.dumps(tags, indent=2))
        return

    if not tags:
        print("No tags found.")
        return

    print(f"{'ID':<20} {'Name'}")
    print("-" * 45)
    for t in tags:
        print(f"{t.get('id', ''):<20} {t.get('name', '')}")
    print(f"\nTotal: {len(tags)} tag(s)")


def create_tag(client: N8nClient, name: str, as_json: bool = False) -> None:
    """Create a tag."""
    result = client.post("/tags", body={"name": name})
    if as_json:
        print(json.dumps(result, indent=2))
        return
    print(f"Created tag: {result.get('id')} - {result.get('name')}")


def get_tag(client: N8nClient, tag_id: str, as_json: bool = False) -> None:
    """Get a tag by ID."""
    tag = client.get(f"/tags/{tag_id}")
    if as_json:
        print(json.dumps(tag, indent=2))
        return
    print(f"ID:   {tag.get('id')}")
    print(f"Name: {tag.get('name')}")


def update_tag(client: N8nClient, tag_id: str, name: str, as_json: bool = False) -> None:
    """Update a tag name."""
    result = client.put(f"/tags/{tag_id}", body={"name": name})
    if as_json:
        print(json.dumps(result, indent=2))
        return
    print(f"Updated tag: {tag_id} -> {name}")


def delete_tag(client: N8nClient, tag_id: str, as_json: bool = False) -> None:
    """Delete a tag."""
    result = client.delete(f"/tags/{tag_id}")
    if as_json:
        print(json.dumps(result, indent=2) if result else '{"deleted": true}')
        return
    print(f"Deleted tag: {tag_id}")
