"""Community package operations for n8n-cli."""

import json
import urllib.parse
from typing import Optional

from .client import N8nClient


def _encode_pkg(name: str) -> str:
    """URL-encode a package name for use in API paths (handles @scope/pkg)."""
    return urllib.parse.quote(name, safe="")


def list_packages(client: N8nClient, as_json: bool = False) -> None:
    """List installed community packages."""
    result = client.get("/community-packages")
    packages = result if isinstance(result, list) else result.get("data", [])

    if as_json:
        print(json.dumps(packages, indent=2))
        return

    if not packages:
        print("No community packages installed.")
        return

    print(f"{'Name':<40} {'Version':<12} {'Nodes'}")
    print("-" * 65)
    for p in packages:
        name = p.get("packageName", "")
        ver = p.get("installedVersion", "")
        nodes = len(p.get("installedNodes", []))
        print(f"{name:<40} {ver:<12} {nodes} node(s)")
    print(f"\nTotal: {len(packages)} package(s)")


def install_package(client: N8nClient, name: str, as_json: bool = False) -> None:
    """Install a community package."""
    result = client.post("/community-packages", body={"name": name})
    if as_json:
        print(json.dumps(result, indent=2))
        return
    print(f"Installed: {name}")


def get_package(client: N8nClient, name: str, as_json: bool = False) -> None:
    """Get details of an installed community package."""
    pkg = client.get(f"/community-packages/{_encode_pkg(name)}")
    if as_json:
        print(json.dumps(pkg, indent=2))
        return
    print(f"Name:      {pkg.get('packageName', '')}")
    print(f"Version:   {pkg.get('installedVersion', '')}")
    nodes = pkg.get("installedNodes", [])
    if nodes:
        print(f"Nodes:")
        for n in nodes:
            print(f"  - {n.get('name', '')} ({n.get('type', '')})")


def update_package(client: N8nClient, name: str, as_json: bool = False) -> None:
    """Update a community package."""
    result = client.patch(f"/community-packages/{_encode_pkg(name)}")
    if as_json:
        print(json.dumps(result, indent=2))
        return
    print(f"Updated: {name}")


def uninstall_package(client: N8nClient, name: str, as_json: bool = False) -> None:
    """Uninstall a community package."""
    result = client.delete(f"/community-packages/{_encode_pkg(name)}")
    if as_json:
        print(json.dumps(result, indent=2) if result else '{"uninstalled": true}')
        return
    print(f"Uninstalled: {name}")
