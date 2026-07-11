"""User operations for n8n-cli."""

import json
from typing import Optional

from .client import N8nClient


def list_users(client: N8nClient, limit: Optional[int] = None, as_json: bool = False) -> None:
    """List all users."""
    if limit is not None:
        users = client.paginate("/users", limit=limit)
    else:
        users = client.paginate("/users")

    if as_json:
        print(json.dumps(users, indent=2))
        return

    if not users:
        print("No users found.")
        return

    print(f"{'ID':<40} {'Email':<30} {'Role':<16} {'Name'}")
    print("-" * 100)
    for u in users:
        uid = u.get("id", "")
        email = u.get("email", "")
        role = u.get("role", "")
        name = f"{u.get('firstName', '')} {u.get('lastName', '')}".strip()
        print(f"{uid:<40} {email:<30} {role:<16} {name}")
    print(f"\nTotal: {len(users)} user(s)")


def get_user(client: N8nClient, user_id: str, as_json: bool = False) -> None:
    """Get a user by ID or email."""
    user = client.get(f"/users/{user_id}")
    if as_json:
        print(json.dumps(user, indent=2))
        return
    print(f"ID:        {user.get('id')}")
    print(f"Email:     {user.get('email')}")
    print(f"Name:      {user.get('firstName', '')} {user.get('lastName', '')}")
    print(f"Role:      {user.get('role', 'N/A')}")
    print(f"Pending:   {user.get('isPending', False)}")
    print(f"Created:   {user.get('createdAt', 'N/A')}")


def delete_user(client: N8nClient, user_id: str, as_json: bool = False) -> None:
    """Delete a user."""
    result = client.delete(f"/users/{user_id}")
    if as_json:
        print(json.dumps(result, indent=2) if result else '{"deleted": true}')
        return
    print(f"Deleted user: {user_id}")


def change_role(client: N8nClient, user_id: str, role: str, as_json: bool = False) -> None:
    """Change a user's global role."""
    result = client.patch(f"/users/{user_id}/role", body={"newRoleName": role})
    if as_json:
        print(json.dumps(result, indent=2) if result else '{"updated": true}')
        return
    print(f"Changed role for {user_id} to {role}")
