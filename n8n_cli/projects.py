"""Project operations for n8n-cli."""

import json
from typing import Optional

from .client import N8nClient


def list_projects(client: N8nClient, limit: Optional[int] = None, as_json: bool = False) -> None:
    """List all projects."""
    if limit is not None:
        projects = client.paginate("/projects", limit=limit)
    else:
        projects = client.paginate("/projects")

    if as_json:
        print(json.dumps(projects, indent=2))
        return

    if not projects:
        print("No projects found.")
        return

    print(f"{'ID':<26} {'Name'}")
    print("-" * 55)
    for p in projects:
        print(f"{p.get('id', ''):<26} {p.get('name', '')}")
    print(f"\nTotal: {len(projects)} project(s)")


def get_project(client: N8nClient, project_id: str, as_json: bool = False) -> None:
    """Get a project by ID."""
    proj = client.get(f"/projects/{project_id}")
    if as_json:
        print(json.dumps(proj, indent=2))
        return
    print(f"ID:   {proj.get('id')}")
    print(f"Name: {proj.get('name')}")
    print(f"Type: {proj.get('type', 'N/A')}")


def create_project(client: N8nClient, name: str, as_json: bool = False) -> None:
    """Create a project."""
    result = client.post("/projects", body={"name": name})
    if as_json:
        print(json.dumps(result, indent=2))
        return
    print(f"Created project: {result.get('id')} - {result.get('name')}")


def update_project(client: N8nClient, project_id: str, name: str, as_json: bool = False) -> None:
    """Update a project."""
    result = client.put(f"/projects/{project_id}", body={"name": name})
    if as_json:
        print(json.dumps(result, indent=2) if result else '{"updated": true}')
        return
    print(f"Updated project: {project_id}")


def delete_project(client: N8nClient, project_id: str, as_json: bool = False) -> None:
    """Delete a project."""
    result = client.delete(f"/projects/{project_id}")
    if as_json:
        print(json.dumps(result, indent=2) if result else '{"deleted": true}')
        return
    print(f"Deleted project: {project_id}")


def list_project_users(client: N8nClient, project_id: str, as_json: bool = False) -> None:
    """List users in a project."""
    result = client.get(f"/projects/{project_id}/users")
    users = result if isinstance(result, list) else result.get("data", [])
    if as_json:
        print(json.dumps(users, indent=2))
        return
    if not users:
        print(f"No users in project {project_id}")
        return
    for u in users:
        print(f"  {u.get('id', '')}  {u.get('email', '')}  {u.get('role', '')}")
