"""Node catalog system for n8n-cli.

Downloads and caches node definitions from the official n8n npm packages.
Auto-checks for updates on every use -- the version check is a single
lightweight HTTP call to the npm registry.
"""

import json
import ssl
import sys
import tarfile
import urllib.request
from io import BytesIO
from pathlib import Path
from typing import Optional

from .exceptions import N8nCatalogError

# Where we store the cached catalog
CACHE_DIR = Path.home() / ".n8n-cli" / "nodes"
CATALOG_FILE = CACHE_DIR / "catalog.json"
META_FILE = CACHE_DIR / "meta.json"

NPM_PACKAGES = [
    "n8n-nodes-base",
    "@n8n/n8n-nodes-langchain",
]

_ctx = ssl.create_default_context()


def _npm_latest_version(package: str) -> str:
    """Check the latest version of an npm package. Fast -- single HTTP call."""
    url = f"https://registry.npmjs.org/{package}/latest"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, context=_ctx, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("version", "")
    except Exception:
        return ""


def _download_nodes_json(package: str, version: str) -> list:
    """Download an npm tarball and extract types/nodes.json from it."""
    # Scoped packages have a different tarball URL pattern
    if package.startswith("@"):
        url = f"https://registry.npmjs.org/{package}/-/{package.split('/')[-1]}-{version}.tgz"
    else:
        url = f"https://registry.npmjs.org/{package}/-/{package}-{version}.tgz"

    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, context=_ctx, timeout=60) as resp:
            tarball = BytesIO(resp.read())
    except Exception as e:
        print(f"  Failed to download {package}@{version}: {e}", file=sys.stderr)
        return []

    try:
        with tarfile.open(fileobj=tarball, mode="r:gz") as tar:
            # The file is at package/dist/types/nodes.json inside the tarball
            for member in tar.getmembers():
                if member.name.endswith("dist/types/nodes.json"):
                    f = tar.extractfile(member)
                    if f:
                        return json.loads(f.read().decode("utf-8"))
    except Exception as e:
        print(f"  Failed to extract nodes from {package}: {e}", file=sys.stderr)

    return []


def _build_catalog_entry(node: dict) -> dict:
    """Build a catalog entry from a full node description.

    Keeps the essential fields for search and planning. The full
    description is stored separately for on-demand access.
    """
    codex = node.get("codex", {})
    categories = codex.get("categories", [])
    subcategories = codex.get("subcategories", {})
    aliases = codex.get("alias", [])
    doc_url = ""
    docs = codex.get("resources", {}).get("primaryDocumentation", [])
    if docs and isinstance(docs, list):
        doc_url = docs[0].get("url", "")

    # Extract operation names from properties
    operations = []
    resources = []
    for prop in node.get("properties", []):
        if prop.get("name") == "operation":
            for opt in prop.get("options", []):
                operations.append(opt.get("name", ""))
        elif prop.get("name") == "resource":
            for opt in prop.get("options", []):
                resources.append(opt.get("name", ""))

    # Credential types
    cred_types = []
    for cred in node.get("credentials", []):
        cred_types.append(cred.get("name", ""))

    return {
        "name": node.get("name", ""),
        "displayName": node.get("displayName", ""),
        "description": node.get("description", ""),
        "group": node.get("group", []),
        "version": node.get("version", 1),
        "defaultVersion": node.get("defaultVersion"),
        "categories": categories,
        "subcategories": subcategories,
        "aliases": aliases,
        "credentials": cred_types,
        "resources": resources,
        "operations": operations,
        "inputs": node.get("inputs", []),
        "outputs": node.get("outputs", []),
        "usableAsTool": node.get("usableAsTool", False),
        "docUrl": doc_url,
    }


def ensure_catalog(force: bool = False, quiet: bool = False) -> dict:
    """Ensure the node catalog exists and is up to date.

    Checks npm for the latest versions on every call. If the cached
    catalog matches, uses it. If not, downloads fresh data.

    Returns the catalog dict with 'nodes' and 'meta' keys.
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Check current cached versions
    cached_meta = {}
    if META_FILE.exists() and not force:
        with open(META_FILE) as f:
            cached_meta = json.load(f)

    # Check latest versions from npm
    needs_update = force
    latest_versions = {}
    npm_reachable = False

    for pkg in NPM_PACKAGES:
        latest = _npm_latest_version(pkg)
        latest_versions[pkg] = latest
        if latest:
            npm_reachable = True
        cached_ver = cached_meta.get("versions", {}).get(pkg, "")
        if latest and latest != cached_ver:
            needs_update = True

    # If npm is unreachable and we have a cached catalog, use it
    if not npm_reachable and not force:
        if CATALOG_FILE.exists():
            with open(CATALOG_FILE) as f:
                return json.load(f)
        # No cache and no network -- can't do anything
        raise N8nCatalogError(
            "Cannot reach npm registry and no cached catalog exists. "
            "Check your internet connection or run 'n8n-cli nodes update' when online."
        )

    if not needs_update and CATALOG_FILE.exists():
        # Catalog is current
        with open(CATALOG_FILE) as f:
            return json.load(f)

    # Download and build fresh catalog
    if not quiet:
        print("Updating node catalog...", file=sys.stderr)

    all_nodes_full = []
    for pkg in NPM_PACKAGES:
        version = latest_versions.get(pkg, "")
        if not version:
            if not quiet:
                print(f"  Skipping {pkg} (couldn't determine version)", file=sys.stderr)
            continue
        if not quiet:
            print(f"  Downloading {pkg}@{version}...", file=sys.stderr)
        nodes = _download_nodes_json(pkg, version)
        if not quiet:
            print(f"  Got {len(nodes)} node definitions", file=sys.stderr)
        for node in nodes:
            node["_package"] = pkg
        all_nodes_full.extend(nodes)

    # Build the index catalog (lightweight)
    index = {}
    for node in all_nodes_full:
        name = node.get("name", "")
        if not name:
            continue
        entry = _build_catalog_entry(node)
        entry["_package"] = node.get("_package", "")

        # For versioned nodes, keep the highest version
        if name in index:
            existing_ver = index[name].get("version", 0)
            new_ver = node.get("version", 0)
            if isinstance(new_ver, list):
                new_ver = max(new_ver) if new_ver else 0
            if isinstance(existing_ver, list):
                existing_ver = max(existing_ver) if existing_ver else 0
            if new_ver <= existing_ver:
                continue

        index[name] = entry

    # Guard: don't persist empty catalog if all downloads failed
    if not index:
        if CATALOG_FILE.exists():
            if not quiet:
                print("  Warning: downloads failed, using cached catalog", file=sys.stderr)
            with open(CATALOG_FILE) as f:
                return json.load(f)
        raise N8nCatalogError(
            "Failed to download any node definitions. "
            "Check your internet connection or try again later."
        )

    catalog = {
        "nodes": index,
        "meta": {
            "versions": latest_versions,
            "node_count": len(index),
        },
    }

    # Save catalog
    with open(CATALOG_FILE, "w") as f:
        json.dump(catalog, f)

    # Save full definitions for on-demand access
    full_path = CACHE_DIR / "full_definitions.json"
    with open(full_path, "w") as f:
        json.dump(all_nodes_full, f)

    # Save meta
    with open(META_FILE, "w") as f:
        json.dump(catalog["meta"], f, indent=2)

    if not quiet:
        print(f"  Catalog updated: {len(index)} nodes", file=sys.stderr)

    return catalog


def search_nodes(query: str, limit: int = 20, as_json: bool = False) -> None:
    """Search the node catalog by keyword."""
    catalog = ensure_catalog(quiet=True)
    nodes = catalog.get("nodes", {})

    query_lower = query.lower()
    results = []

    for name, node in nodes.items():
        score = 0
        # Exact name match
        if query_lower == name.lower():
            score = 100
        elif query_lower in name.lower():
            score = 50
        # Display name match
        elif query_lower in node.get("displayName", "").lower():
            score = 40
        # Description match
        elif query_lower in node.get("description", "").lower():
            score = 20
        # Alias match
        elif any(query_lower in a.lower() for a in node.get("aliases", [])):
            score = 30
        # Category match
        elif any(query_lower in c.lower() for c in node.get("categories", [])):
            score = 10
        # Resource/operation match
        elif any(query_lower in r.lower() for r in node.get("resources", [])):
            score = 15
        elif any(query_lower in o.lower() for o in node.get("operations", [])):
            score = 15

        if score > 0:
            results.append((score, name, node))

    results.sort(key=lambda x: (-x[0], x[1]))
    results = results[:limit]

    if as_json:
        print(json.dumps([r[2] for r in results], indent=2))
        return

    if not results:
        print(f"No nodes matching '{query}'.")
        return

    print(f"{'Node':<30} {'Display Name':<25} {'Description'}")
    print("-" * 90)
    for _, name, node in results:
        display = node.get("displayName", "")[:23]
        desc = node.get("description", "")[:40]
        print(f"{name:<30} {display:<25} {desc}")
    print(f"\n{len(results)} result(s)")


def get_node(node_name: str, full: bool = False, as_json: bool = False) -> None:
    """Get details for a specific node type."""
    catalog = ensure_catalog(quiet=True)
    nodes = catalog.get("nodes", {})

    # Try exact match first, then case-insensitive
    node = nodes.get(node_name)
    if not node:
        for name, n in nodes.items():
            if name.lower() == node_name.lower():
                node = n
                node_name = name
                break

    if not node:
        raise N8nCatalogError(f"Node '{node_name}' not found. Try: n8n-cli nodes search {node_name}")

    if full:
        # Load full definition from the full_definitions file
        full_path = CACHE_DIR / "full_definitions.json"
        if full_path.exists():
            with open(full_path) as f:
                all_defs = json.load(f)
            for d in all_defs:
                if d.get("name") == node_name:
                    if as_json:
                        print(json.dumps(d, indent=2))
                    else:
                        print(json.dumps(d, indent=2))
                    return
        raise N8nCatalogError("Full definition not available. Run: n8n-cli nodes update")

    if as_json:
        print(json.dumps(node, indent=2))
        return

    print(f"Name:         {node_name}")
    print(f"Display Name: {node.get('displayName', '')}")
    print(f"Description:  {node.get('description', '')}")
    print(f"Group:        {', '.join(node.get('group', []))}")
    ver = node.get("version", "")
    if isinstance(ver, list):
        print(f"Versions:     {', '.join(str(v) for v in ver)}")
    else:
        print(f"Version:      {ver}")
    print(f"AI Tool:      {'Yes' if node.get('usableAsTool') else 'No'}")

    creds = node.get("credentials", [])
    if creds:
        print(f"Credentials:  {', '.join(creds)}")

    cats = node.get("categories", [])
    if cats:
        print(f"Categories:   {', '.join(cats)}")

    resources = node.get("resources", [])
    if resources:
        print(f"Resources:    {', '.join(resources)}")

    ops = node.get("operations", [])
    if ops:
        print(f"Operations:   {', '.join(ops)}")

    aliases = node.get("aliases", [])
    if aliases:
        print(f"Aliases:      {', '.join(aliases)}")

    doc = node.get("docUrl", "")
    if doc:
        print(f"Docs:         {doc}")


def list_nodes(
    group: Optional[str] = None,
    category: Optional[str] = None,
    credential: Optional[str] = None,
    ai_tools: bool = False,
    limit: Optional[int] = None,
    as_json: bool = False,
) -> None:
    """List all nodes with optional filters."""
    catalog = ensure_catalog(quiet=True)
    nodes = catalog.get("nodes", {})

    results = []
    for name, node in nodes.items():
        # Filter by group (trigger, action, transform, etc.)
        if group:
            if group.lower() not in [g.lower() for g in node.get("group", [])]:
                continue

        # Filter by category
        if category:
            if category.lower() not in [c.lower() for c in node.get("categories", [])]:
                continue

        # Filter by credential type
        if credential:
            if credential.lower() not in [c.lower() for c in node.get("credentials", [])]:
                continue

        # Filter AI-usable tools only
        if ai_tools and not node.get("usableAsTool"):
            continue

        results.append((name, node))

    results.sort(key=lambda x: x[0])

    if limit:
        results = results[:limit]

    if as_json:
        print(json.dumps([r[1] for r in results], indent=2))
        return

    if not results:
        print("No nodes matching filters.")
        return

    print(f"{'Node':<30} {'Display Name':<25} {'Group':<12} {'Creds'}")
    print("-" * 85)
    for name, node in results:
        display = node.get("displayName", "")[:23]
        groups = ",".join(node.get("group", []))[:10]
        creds = ",".join(node.get("credentials", []))[:20]
        print(f"{name:<30} {display:<25} {groups:<12} {creds}")
    print(f"\nTotal: {len(results)} node(s)")


def update_catalog(as_json: bool = False) -> None:
    """Force-update the node catalog from npm."""
    catalog = ensure_catalog(force=True)
    meta = catalog.get("meta", {})
    if as_json:
        print(json.dumps(meta, indent=2))
    else:
        print(f"Node catalog updated.")
        for pkg, ver in meta.get("versions", {}).items():
            print(f"  {pkg}: {ver}")
        print(f"  Total nodes: {meta.get('node_count', 0)}")


def catalog_info(as_json: bool = False) -> None:
    """Show catalog status without updating."""
    if not META_FILE.exists():
        print("No catalog cached. Run: n8n-cli nodes update")
        return

    with open(META_FILE) as f:
        meta = json.load(f)

    if as_json:
        print(json.dumps(meta, indent=2))
        return

    print(f"Cached node catalog:")
    for pkg, ver in meta.get("versions", {}).items():
        print(f"  {pkg}: {ver}")
    print(f"  Total nodes: {meta.get('node_count', 0)}")

    # Check if update available
    for pkg in NPM_PACKAGES:
        latest = _npm_latest_version(pkg)
        cached = meta.get("versions", {}).get(pkg, "")
        if latest and latest != cached:
            print(f"\n  Update available: {pkg} {cached} -> {latest}")
