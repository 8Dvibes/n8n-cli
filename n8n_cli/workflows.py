"""Workflow operations for n8n-cli."""

import json
import sys
from typing import Optional

from .client import N8nClient


def list_workflows(
    client: N8nClient,
    active: Optional[bool] = None,
    tags: Optional[str] = None,
    name: Optional[str] = None,
    project_id: Optional[str] = None,
    limit: Optional[int] = None,
    as_json: bool = False,
) -> None:
    """List workflows with optional filters."""
    params = {}
    if active is not None:
        params["active"] = str(active).lower()
    if tags:
        params["tags"] = tags
    if name:
        params["name"] = name
    if project_id:
        params["projectId"] = project_id

    if limit:
        workflows = client.paginate("/workflows", params=params, limit=limit)
    else:
        workflows = client.paginate("/workflows", params=params)

    if as_json:
        print(json.dumps(workflows, indent=2))
        return

    if not workflows:
        print("No workflows found.")
        return

    # Table output
    print(f"{'ID':<20} {'Active':<8} {'Name'}")
    print("-" * 70)
    for wf in workflows:
        wid = wf.get("id", "")
        name_str = wf.get("name", "untitled")
        active_str = "Yes" if wf.get("active") else "No"
        print(f"{wid:<20} {active_str:<8} {name_str}")
    print(f"\nTotal: {len(workflows)} workflow(s)")


def get_workflow(client: N8nClient, workflow_id: str, as_json: bool = False) -> None:
    """Get a single workflow by ID."""
    wf = client.get(f"/workflows/{workflow_id}")

    if as_json:
        print(json.dumps(wf, indent=2))
        return

    print(f"ID:       {wf.get('id')}")
    print(f"Name:     {wf.get('name')}")
    print(f"Active:   {wf.get('active')}")
    print(f"Created:  {wf.get('createdAt', 'N/A')}")
    print(f"Updated:  {wf.get('updatedAt', 'N/A')}")
    tags = wf.get("tags", [])
    if tags:
        tag_names = [t.get("name", t.get("id", "")) for t in tags]
        print(f"Tags:     {', '.join(tag_names)}")
    nodes = wf.get("nodes", [])
    print(f"Nodes:    {len(nodes)}")
    for n in nodes:
        print(f"  - {n.get('name')} ({n.get('type')})")


def create_workflow(client: N8nClient, file_path: str, as_json: bool = False) -> None:
    """Create a workflow from a JSON file."""
    with open(file_path) as f:
        data = json.load(f)

    result = client.post("/workflows", body=data)

    if as_json:
        print(json.dumps(result, indent=2))
        return

    print(f"Created workflow: {result.get('id')} - {result.get('name')}")


def update_workflow(client: N8nClient, workflow_id: str, file_path: str, as_json: bool = False) -> None:
    """Update a workflow from a JSON file."""
    with open(file_path) as f:
        data = json.load(f)

    result = client.put(f"/workflows/{workflow_id}", body=data)

    if as_json:
        print(json.dumps(result, indent=2))
        return

    print(f"Updated workflow: {result.get('id')} - {result.get('name')}")


def delete_workflow(client: N8nClient, workflow_id: str, as_json: bool = False) -> None:
    """Delete a workflow."""
    result = client.delete(f"/workflows/{workflow_id}")

    if as_json:
        print(json.dumps(result, indent=2) if result else '{"deleted": true}')
        return

    print(f"Deleted workflow: {workflow_id}")


def activate_workflow(client: N8nClient, workflow_id: str, as_json: bool = False) -> None:
    """Activate a workflow."""
    result = client.post(f"/workflows/{workflow_id}/activate")

    if as_json:
        print(json.dumps(result, indent=2))
        return

    print(f"Activated: {result.get('id')} - {result.get('name')}")


def deactivate_workflow(client: N8nClient, workflow_id: str, as_json: bool = False) -> None:
    """Deactivate a workflow."""
    result = client.post(f"/workflows/{workflow_id}/deactivate")

    if as_json:
        print(json.dumps(result, indent=2))
        return

    print(f"Deactivated: {result.get('id')} - {result.get('name')}")


def export_workflow(client: N8nClient, workflow_id: str, output: Optional[str] = None, as_json: bool = True) -> None:
    """Export a workflow to JSON file."""
    wf = client.get(f"/workflows/{workflow_id}")

    if output:
        with open(output, "w") as f:
            json.dump(wf, f, indent=2)
        print(f"Exported workflow '{wf.get('name')}' to {output}")
    else:
        print(json.dumps(wf, indent=2))


def import_workflow(
    client: N8nClient,
    file_path: str,
    activate: bool = False,
    as_json: bool = False,
) -> None:
    """Import a workflow from a JSON file, optionally activating it."""
    with open(file_path) as f:
        data = json.load(f)

    # Strip fields that shouldn't be in a create payload
    for key in ("id", "createdAt", "updatedAt", "versionId"):
        data.pop(key, None)

    result = client.post("/workflows", body=data)
    wf_id = result.get("id")

    if activate and wf_id:
        client.post(f"/workflows/{wf_id}/activate")
        result["active"] = True

    if as_json:
        print(json.dumps(result, indent=2))
        return

    status = "active" if activate else "inactive"
    print(f"Imported workflow: {wf_id} - {result.get('name')} ({status})")


def archive_workflow(client: N8nClient, workflow_id: str, as_json: bool = False) -> None:
    """Archive a workflow."""
    result = client.post(f"/workflows/{workflow_id}/archive")
    if as_json:
        print(json.dumps(result, indent=2))
        return
    print(f"Archived: {workflow_id}")


def unarchive_workflow(client: N8nClient, workflow_id: str, as_json: bool = False) -> None:
    """Unarchive a workflow."""
    result = client.post(f"/workflows/{workflow_id}/unarchive")
    if as_json:
        print(json.dumps(result, indent=2))
        return
    print(f"Unarchived: {workflow_id}")


def transfer_workflow(client: N8nClient, workflow_id: str, project_id: str, as_json: bool = False) -> None:
    """Transfer a workflow to another project."""
    result = client.put(f"/workflows/{workflow_id}/transfer", body={"destinationProjectId": project_id})
    if as_json:
        print(json.dumps(result, indent=2) if result else '{"transferred": true}')
        return
    print(f"Transferred workflow {workflow_id} to project {project_id}")


def get_workflow_tags(client: N8nClient, workflow_id: str, as_json: bool = False) -> None:
    """Get tags for a workflow."""
    result = client.get(f"/workflows/{workflow_id}/tags")
    if as_json:
        print(json.dumps(result, indent=2))
        return
    tags = result if isinstance(result, list) else result.get("data", [])
    if not tags:
        print(f"No tags on workflow {workflow_id}")
        return
    for t in tags:
        print(f"  {t.get('id', '')}  {t.get('name', '')}")


def update_workflow_tags(client: N8nClient, workflow_id: str, tag_ids: list, as_json: bool = False) -> None:
    """Set tags on a workflow (replaces existing)."""
    body = [{"id": tid} for tid in tag_ids]
    result = client.put(f"/workflows/{workflow_id}/tags", body=body)
    if as_json:
        print(json.dumps(result, indent=2))
        return
    print(f"Updated tags on workflow {workflow_id}")
