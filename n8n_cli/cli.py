"""CLI entrypoint for n8n-cli. Uses argparse only (no external deps)."""

import argparse
import json
import sys

from . import __version__
from .client import N8nClient
from .config import get_profile, require_profile, load_config, save_config
from .exceptions import N8nError, N8nApiError, N8nConfigError


def _client(args) -> N8nClient:
    """Build an N8nClient from CLI args."""
    profile = require_profile(getattr(args, "profile", None))
    return N8nClient(profile["api_url"], profile["api_key"])


def _json(args) -> bool:
    return getattr(args, "json", False)


# ── Health ───────────────────────────────────────────────────────────

def cmd_health(args):
    client = _client(args)
    # Try listing workflows with limit=1 as a health check.
    # If the API key is invalid or server is down, N8nApiError or
    # N8nConnectionError propagates to main()'s central handler.
    client.get("/workflows", params={"limit": 1})
    profile = get_profile(getattr(args, "profile", None))
    if _json(args):
        print(json.dumps({
            "status": "ok",
            "profile": profile["profile_name"],
            "api_url": profile["api_url"],
            "workflows_accessible": True,
        }, indent=2))
    else:
        from .output import Output
        out = Output()
        out.heading("n8n Health Check")
        out.success("Connected")
        out.kv("Profile", profile["profile_name"])
        out.kv("API URL", profile["api_url"])
        out.kv("Auth", "Valid")
        out.blank()


# ── Discover ─────────────────────────────────────────────────────────

def cmd_discover(args):
    """Show API capabilities (discover endpoint)."""
    client = _client(args)
    result = client.get("/discover")
    if _json(args):
        print(json.dumps(result, indent=2))
    else:
        if isinstance(result, dict):
            for key, value in result.items():
                print(f"{key}: {json.dumps(value)}")
        else:
            print(json.dumps(result, indent=2))


# ── Config ───────────────────────────────────────────────────────────

def _mask_key(key: str) -> str:
    """Mask an API key, showing only the last 4 chars."""
    if not key:
        return "(not set)"
    if len(key) <= 4:
        return "****"
    return "****" + key[-4:]


def cmd_config_show(args):
    profile = get_profile(getattr(args, "profile", None))
    if _json(args):
        safe = {**profile, "api_key": _mask_key(profile["api_key"])}
        print(json.dumps(safe, indent=2))
    else:
        print(f"Profile:  {profile['profile_name']}")
        print(f"API URL:  {profile['api_url'] or '(not set)'}")
        print(f"API Key:  {_mask_key(profile['api_key'])}")


def cmd_config_set_profile(args):
    config = load_config()
    profiles = config.setdefault("profiles", {})
    profiles[args.name] = {
        "api_url": args.url,
        "api_key": args.key,
    }
    if args.default:
        config["default_profile"] = args.name
    save_config(config)
    print(f"Profile '{args.name}' saved.")
    if args.default:
        print(f"Set as default profile.")


def cmd_config_list_profiles(args):
    config = load_config()
    default = config.get("default_profile", "default")
    profiles = config.get("profiles", {})
    if _json(args):
        print(json.dumps({"default": default, "profiles": list(profiles.keys())}, indent=2))
        return
    for name in profiles:
        marker = " (default)" if name == default else ""
        url = profiles[name].get("api_url", "")
        print(f"  {name}{marker}: {url}")


def cmd_config_use(args):
    config = load_config()
    if args.name not in config.get("profiles", {}):
        raise N8nConfigError(f"Profile '{args.name}' not found.")
    config["default_profile"] = args.name
    save_config(config)
    print(f"Now using profile: {args.name}")


def cmd_config_delete_profile(args):
    config = load_config()
    profiles = config.get("profiles", {})
    if args.name not in profiles:
        raise N8nConfigError(f"Profile '{args.name}' not found.")
    del profiles[args.name]
    if config.get("default_profile") == args.name:
        config["default_profile"] = next(iter(profiles), "default")
    save_config(config)
    print(f"Deleted profile: {args.name}")


# ── Workflows ────────────────────────────────────────────────────────

def cmd_workflows_list(args):
    from .workflows import list_workflows
    client = _client(args)
    active = None
    if args.active:
        active = True
    elif args.inactive:
        active = False
    list_workflows(client, active=active, tags=args.tag, name=args.name,
                   project_id=args.project_id, limit=args.limit, as_json=_json(args))


def cmd_workflows_get(args):
    from .workflows import get_workflow
    get_workflow(_client(args), args.id, as_json=_json(args))


def cmd_workflows_create(args):
    from .workflows import create_workflow
    create_workflow(_client(args), args.file, as_json=_json(args))


def cmd_workflows_update(args):
    from .workflows import update_workflow
    update_workflow(_client(args), args.id, args.file, as_json=_json(args))


def cmd_workflows_delete(args):
    client = _client(args)
    if getattr(args, "dry_run", False):
        wf = client.get(f"/workflows/{args.id}")
        if _json(args):
            print(json.dumps({"dry_run": True, "action": "delete",
                              "id": args.id, "name": wf.get("name"),
                              "active": wf.get("active")}, indent=2))
        else:
            print(f"DRY RUN: Would delete workflow '{wf.get('name')}' ({args.id})")
            if wf.get("active"):
                print("  WARNING: This workflow is currently active.")
        return
    from .workflows import delete_workflow
    delete_workflow(client, args.id, as_json=_json(args))


def cmd_workflows_activate(args):
    client = _client(args)
    if getattr(args, "dry_run", False):
        wf = client.get(f"/workflows/{args.id}")
        if _json(args):
            print(json.dumps({"dry_run": True, "action": "activate",
                              "id": args.id, "name": wf.get("name"),
                              "active": wf.get("active")}, indent=2))
        else:
            status = "already active" if wf.get("active") else "currently inactive"
            print(f"DRY RUN: Would activate '{wf.get('name')}' ({args.id}, {status})")
        return
    from .workflows import activate_workflow
    activate_workflow(client, args.id, as_json=_json(args))


def cmd_workflows_deactivate(args):
    client = _client(args)
    if getattr(args, "dry_run", False):
        wf = client.get(f"/workflows/{args.id}")
        if _json(args):
            print(json.dumps({"dry_run": True, "action": "deactivate",
                              "id": args.id, "name": wf.get("name"),
                              "active": wf.get("active")}, indent=2))
        else:
            status = "currently active" if wf.get("active") else "already inactive"
            print(f"DRY RUN: Would deactivate '{wf.get('name')}' ({args.id}, {status})")
        return
    from .workflows import deactivate_workflow
    deactivate_workflow(client, args.id, as_json=_json(args))


def cmd_workflows_export(args):
    from .workflows import export_workflow
    export_workflow(_client(args), args.id, output=args.output, as_json=_json(args))


def cmd_workflows_import(args):
    from .workflows import import_workflow
    import_workflow(_client(args), args.file, activate=args.activate, as_json=_json(args))


def cmd_workflows_archive(args):
    from .workflows import archive_workflow
    archive_workflow(_client(args), args.id, as_json=_json(args))


def cmd_workflows_unarchive(args):
    from .workflows import unarchive_workflow
    unarchive_workflow(_client(args), args.id, as_json=_json(args))


def cmd_workflows_transfer(args):
    from .workflows import transfer_workflow
    transfer_workflow(_client(args), args.id, args.project_id, as_json=_json(args))


def cmd_workflows_tags(args):
    from .workflows import get_workflow_tags
    get_workflow_tags(_client(args), args.id, as_json=_json(args))


def cmd_workflows_set_tags(args):
    from .workflows import update_workflow_tags
    update_workflow_tags(_client(args), args.id, args.tag_ids, as_json=_json(args))


# ── Executions ───────────────────────────────────────────────────────

def cmd_executions_list(args):
    from .executions import list_executions
    list_executions(_client(args), workflow_id=args.workflow_id, status=args.status,
                    limit=args.limit, as_json=_json(args))


def cmd_executions_get(args):
    from .executions import get_execution
    get_execution(_client(args), args.id, as_json=_json(args))


def cmd_executions_retry(args):
    from .executions import retry_execution
    retry_execution(_client(args), args.id, as_json=_json(args))


def cmd_executions_delete(args):
    from .executions import delete_execution
    delete_execution(_client(args), args.id, as_json=_json(args))


def cmd_executions_stop(args):
    from .executions import stop_execution
    stop_execution(_client(args), args.id, as_json=_json(args))


def cmd_executions_tail(args):
    from .executions import tail_executions
    tail_executions(
        _client(args),
        workflow_id=args.workflow_id,
        status=args.status,
        interval=args.interval,
        as_json=_json(args),
    )


# ── Credentials ──────────────────────────────────────────────────────

def cmd_credentials_list(args):
    from .credentials import list_credentials
    list_credentials(_client(args), cred_type=args.type, limit=args.limit, as_json=_json(args))


def cmd_credentials_get(args):
    from .credentials import get_credential
    get_credential(_client(args), args.id, as_json=_json(args))


def cmd_credentials_schema(args):
    from .credentials import get_credential_schema
    get_credential_schema(_client(args), args.type_name, as_json=_json(args))


def cmd_credentials_create(args):
    from .credentials import create_credential
    create_credential(_client(args), args.file, as_json=_json(args))


def cmd_credentials_delete(args):
    from .credentials import delete_credential
    delete_credential(_client(args), args.id, as_json=_json(args))


def cmd_credentials_transfer(args):
    from .credentials import transfer_credential
    transfer_credential(_client(args), args.id, args.project_id, as_json=_json(args))


# ── Tags ─────────────────────────────────────────────────────────────

def cmd_tags_list(args):
    from .tags import list_tags
    list_tags(_client(args), limit=args.limit, as_json=_json(args))


def cmd_tags_create(args):
    from .tags import create_tag
    create_tag(_client(args), args.name, as_json=_json(args))


def cmd_tags_get(args):
    from .tags import get_tag
    get_tag(_client(args), args.id, as_json=_json(args))


def cmd_tags_update(args):
    from .tags import update_tag
    update_tag(_client(args), args.id, args.name, as_json=_json(args))


def cmd_tags_delete(args):
    from .tags import delete_tag
    delete_tag(_client(args), args.id, as_json=_json(args))


# ── Variables ────────────────────────────────────────────────────────

def cmd_variables_list(args):
    from .variables import list_variables
    list_variables(_client(args), limit=args.limit, as_json=_json(args))


def cmd_variables_create(args):
    from .variables import create_variable
    create_variable(_client(args), args.key, args.value, as_json=_json(args))


def cmd_variables_get(args):
    from .variables import get_variable
    get_variable(_client(args), args.id, as_json=_json(args))


def cmd_variables_update(args):
    from .variables import update_variable
    update_variable(_client(args), args.id, key=args.key, value=args.value, as_json=_json(args))


def cmd_variables_delete(args):
    from .variables import delete_variable
    delete_variable(_client(args), args.id, as_json=_json(args))


# ── Projects ─────────────────────────────────────────────────────────

def cmd_projects_list(args):
    from .projects import list_projects
    list_projects(_client(args), limit=args.limit, as_json=_json(args))


def cmd_projects_get(args):
    from .projects import get_project
    get_project(_client(args), args.id, as_json=_json(args))


def cmd_projects_create(args):
    from .projects import create_project
    create_project(_client(args), args.name, as_json=_json(args))


def cmd_projects_update(args):
    from .projects import update_project
    update_project(_client(args), args.id, args.name, as_json=_json(args))


def cmd_projects_delete(args):
    from .projects import delete_project
    delete_project(_client(args), args.id, as_json=_json(args))


def cmd_projects_users(args):
    from .projects import list_project_users
    list_project_users(_client(args), args.id, as_json=_json(args))


# ── Users ────────────────────────────────────────────────────────────

def cmd_users_list(args):
    from .users import list_users
    list_users(_client(args), limit=args.limit, as_json=_json(args))


def cmd_users_get(args):
    from .users import get_user
    get_user(_client(args), args.id, as_json=_json(args))


def cmd_users_delete(args):
    from .users import delete_user
    delete_user(_client(args), args.id, as_json=_json(args))


def cmd_users_change_role(args):
    from .users import change_role
    change_role(_client(args), args.id, args.role, as_json=_json(args))


# ── Audit ────────────────────────────────────────────────────────────

def cmd_audit(args):
    from .audit import generate_audit
    generate_audit(_client(args), categories=args.categories, as_json=_json(args))


# ── Source Control ───────────────────────────────────────────────────

def cmd_source_control_pull(args):
    from .source_control import pull
    pull(_client(args), force=args.force, as_json=_json(args))


# ── Community Packages ───────────────────────────────────────────────

def cmd_packages_list(args):
    from .community_packages import list_packages
    list_packages(_client(args), as_json=_json(args))


def cmd_packages_install(args):
    from .community_packages import install_package
    install_package(_client(args), args.name, as_json=_json(args))


def cmd_packages_get(args):
    from .community_packages import get_package
    get_package(_client(args), args.name, as_json=_json(args))


def cmd_packages_update(args):
    from .community_packages import update_package
    update_package(_client(args), args.name, as_json=_json(args))


def cmd_packages_uninstall(args):
    from .community_packages import uninstall_package
    uninstall_package(_client(args), args.name, as_json=_json(args))


# ── Nodes (local catalog) ───────────────────────────────────────────

def cmd_nodes_search(args):
    from .nodes import search_nodes
    search_nodes(args.query, limit=args.limit or 20, as_json=_json(args))


def cmd_nodes_get(args):
    from .nodes import get_node
    get_node(args.name, full=args.full, as_json=_json(args))


def cmd_nodes_list(args):
    from .nodes import list_nodes
    list_nodes(
        group=args.group, category=args.category,
        credential=args.credential, ai_tools=args.ai_tools,
        limit=args.limit, as_json=_json(args),
    )


def cmd_nodes_update(args):
    from .nodes import update_catalog
    update_catalog(as_json=_json(args))


def cmd_nodes_info(args):
    from .nodes import catalog_info
    catalog_info(as_json=_json(args))


# ── Webhooks ─────────────────────────────────────────────────────────

def cmd_webhooks_test(args):
    from .webhooks import test_webhook
    test_webhook(_client(args), args.workflow_id, data=args.data,
                 method=args.method, as_json=_json(args))


def cmd_webhooks_list(args):
    from .webhooks import list_webhooks
    list_webhooks(_client(args), as_json=_json(args))


# ── Skills (Claude Code) ─────────────────────────────────────────────

def cmd_skills_list(args):
    from . import skills as _skills
    _skills.cmd_list(as_json=_json(args))


def cmd_skills_install(args):
    from . import skills as _skills
    _skills.cmd_install(names=args.names, force=args.force, as_json=_json(args))


def cmd_skills_uninstall(args):
    from . import skills as _skills
    _skills.cmd_uninstall(names=args.names, as_json=_json(args))


def cmd_skills_path(args):
    from . import skills as _skills
    _skills.cmd_path(as_json=_json(args))


def cmd_skills_doctor(args):
    from . import skills as _skills
    _skills.cmd_doctor(as_json=_json(args))


def cmd_workflows_clear_tags(args):
    from .workflows import clear_workflow_tags
    clear_workflow_tags(_client(args), args.id, as_json=_json(args))


# ── Completion ──────────────────────────────────────────────────────

def cmd_completion(args):
    """Print shell completion script."""
    from .completions import generate_bash, generate_zsh
    parser = build_parser()
    if args.shell == "zsh":
        print(generate_zsh(parser))
    else:
        print(generate_bash(parser))


def cmd_workflows_validate(args):
    from .workflows import validate_workflow
    validate_workflow(args.file, as_json=_json(args))


def cmd_workflows_diff(args):
    """Compare a local workflow JSON against the live version on n8n."""
    import difflib
    client = _client(args)

    # Get live workflow
    live = client.get(f"/workflows/{args.id}")
    live_json = json.dumps(live, indent=2, sort_keys=True).splitlines(keepends=True)

    # Get local file
    with open(args.file) as f:
        local = json.load(f)
    local_json = json.dumps(local, indent=2, sort_keys=True).splitlines(keepends=True)

    diff = list(difflib.unified_diff(
        live_json, local_json,
        fromfile=f"live:{args.id}",
        tofile=args.file,
    ))

    if _json(args):
        print(json.dumps({
            "has_changes": len(diff) > 0,
            "additions": sum(1 for l in diff if l.startswith("+") and not l.startswith("+++")),
            "deletions": sum(1 for l in diff if l.startswith("-") and not l.startswith("---")),
            "diff": "".join(diff),
        }, indent=2))
    else:
        if diff:
            print(f"Differences between live:{args.id} and {args.file}:")
            print()
            for line in diff:
                print(line, end="")
        else:
            print(f"No differences between live:{args.id} and {args.file}")


def cmd_open(args):
    """Open n8n web UI in the browser."""
    import webbrowser
    profile = get_profile(getattr(args, "profile", None))
    api_url = profile.get("api_url", "")
    if not api_url:
        from .exceptions import N8nConfigError
        raise N8nConfigError("No API URL configured.")

    # Derive base URL
    from .webhooks import _webhook_base_url
    base = _webhook_base_url(api_url)

    target = getattr(args, "target", None)
    target_id = getattr(args, "target_id", None)

    if target == "workflow" and target_id:
        url = f"{base}/workflow/{target_id}"
    elif target == "execution" and target_id:
        url = f"{base}/executions/{target_id}"
    elif target == "settings":
        url = f"{base}/settings"
    elif target == "credentials":
        url = f"{base}/credentials"
    else:
        url = base

    if _json(args):
        print(json.dumps({"url": url}, indent=2))
    else:
        print(f"Opening: {url}")
        webbrowser.open(url)


# ── API (raw escape hatch) ──────────────────────────────────────────

def cmd_api(args):
    """Raw API call to any n8n REST endpoint.

    This is the escape hatch for endpoints the CLI doesn't cover yet.
    Useful for AI agents that need full API access without waiting for
    a dedicated command to be added.
    """
    client = _client(args)
    body = None
    if args.data:
        body = json.loads(args.data)
    elif args.data_file:
        with open(args.data_file) as f:
            body = json.load(f)

    result = client._request(
        args.method.upper(),
        args.path,
        body=body,
    )

    if result is not None:
        print(json.dumps(result, indent=2))
    else:
        print("{}")


# ── Parser Builder ───────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="n8n-cli",
        description="CLI tool for the n8n REST API",
    )
    parser.add_argument("-v", "--version", action="version", version=f"n8n-cli {__version__}")
    parser.add_argument("-p", "--profile", help="Config profile to use")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")

    sub = parser.add_subparsers(dest="command", help="Available commands")

    # ── health ──
    p = sub.add_parser("health", help="Check n8n instance status")
    p.set_defaults(func=cmd_health)

    # ── discover ──
    p = sub.add_parser("discover", help="Show API capabilities")
    p.set_defaults(func=cmd_discover)

    # ── config ──
    cfg = sub.add_parser("config", help="Manage configuration")
    cfg_sub = cfg.add_subparsers(dest="config_cmd")

    p = cfg_sub.add_parser("show", help="Show current config")
    p.set_defaults(func=cmd_config_show)

    p = cfg_sub.add_parser("set-profile", help="Create or update a profile")
    p.add_argument("name", help="Profile name")
    p.add_argument("--url", required=True, help="n8n API URL")
    p.add_argument("--key", required=True, help="n8n API key")
    p.add_argument("--default", action="store_true", help="Set as default profile")
    p.set_defaults(func=cmd_config_set_profile)

    p = cfg_sub.add_parser("list-profiles", help="List all profiles")
    p.set_defaults(func=cmd_config_list_profiles)

    p = cfg_sub.add_parser("use", help="Switch default profile")
    p.add_argument("name", help="Profile name to use")
    p.set_defaults(func=cmd_config_use)

    p = cfg_sub.add_parser("delete-profile", help="Delete a profile")
    p.add_argument("name", help="Profile name to delete")
    p.set_defaults(func=cmd_config_delete_profile)

    # ── workflows ──
    wf = sub.add_parser("workflows", aliases=["wf"], help="Workflow operations")
    wf_sub = wf.add_subparsers(dest="wf_cmd")

    p = wf_sub.add_parser("list", aliases=["ls"], help="List workflows")
    active_group = p.add_mutually_exclusive_group()
    active_group.add_argument("--active", action="store_true", help="Only active workflows")
    active_group.add_argument("--inactive", action="store_true", help="Only inactive workflows")
    p.add_argument("--tag", help="Filter by tag name")
    p.add_argument("--name", help="Filter by workflow name")
    p.add_argument("--project-id", help="Filter by project ID")
    p.add_argument("--limit", type=int, help="Max results")
    p.set_defaults(func=cmd_workflows_list)

    p = wf_sub.add_parser("get", help="Get workflow details")
    p.add_argument("id", help="Workflow ID")
    p.set_defaults(func=cmd_workflows_get)

    p = wf_sub.add_parser("create", help="Create workflow from JSON")
    p.add_argument("file", help="JSON file path")
    p.set_defaults(func=cmd_workflows_create)

    p = wf_sub.add_parser("update", help="Update workflow from JSON")
    p.add_argument("id", help="Workflow ID")
    p.add_argument("file", help="JSON file path")
    p.set_defaults(func=cmd_workflows_update)

    p = wf_sub.add_parser("delete", aliases=["rm"], help="Delete a workflow")
    p.add_argument("id", help="Workflow ID")
    p.add_argument("--dry-run", action="store_true",
                   help="Show what would be deleted without doing it")
    p.set_defaults(func=cmd_workflows_delete)

    p = wf_sub.add_parser("activate", help="Activate a workflow")
    p.add_argument("id", help="Workflow ID")
    p.add_argument("--dry-run", action="store_true",
                   help="Show what would be activated without doing it")
    p.set_defaults(func=cmd_workflows_activate)

    p = wf_sub.add_parser("deactivate", help="Deactivate a workflow")
    p.add_argument("id", help="Workflow ID")
    p.add_argument("--dry-run", action="store_true",
                   help="Show what would be deactivated without doing it")
    p.set_defaults(func=cmd_workflows_deactivate)

    p = wf_sub.add_parser("export", help="Export workflow to JSON")
    p.add_argument("id", help="Workflow ID")
    p.add_argument("-o", "--output", help="Output file path")
    p.set_defaults(func=cmd_workflows_export)

    p = wf_sub.add_parser("import", help="Import workflow from JSON")
    p.add_argument("file", help="JSON file path")
    p.add_argument("--activate", action="store_true", help="Activate after import")
    p.set_defaults(func=cmd_workflows_import)

    p = wf_sub.add_parser("archive", help="Archive a workflow")
    p.add_argument("id", help="Workflow ID")
    p.set_defaults(func=cmd_workflows_archive)

    p = wf_sub.add_parser("unarchive", help="Unarchive a workflow")
    p.add_argument("id", help="Workflow ID")
    p.set_defaults(func=cmd_workflows_unarchive)

    p = wf_sub.add_parser("transfer", help="Transfer workflow to project")
    p.add_argument("id", help="Workflow ID")
    p.add_argument("project_id", help="Destination project ID")
    p.set_defaults(func=cmd_workflows_transfer)

    p = wf_sub.add_parser("tags", help="Get workflow tags")
    p.add_argument("id", help="Workflow ID")
    p.set_defaults(func=cmd_workflows_tags)

    p = wf_sub.add_parser("set-tags", help="Set workflow tags")
    p.add_argument("id", help="Workflow ID")
    p.add_argument("tag_ids", nargs="+", help="Tag IDs to set")
    p.set_defaults(func=cmd_workflows_set_tags)

    p = wf_sub.add_parser("clear-tags", help="Remove all tags from a workflow")
    p.add_argument("id", help="Workflow ID")
    p.set_defaults(func=cmd_workflows_clear_tags)

    p = wf_sub.add_parser("validate", help="Validate workflow JSON before import")
    p.add_argument("file", help="JSON file path to validate")
    p.set_defaults(func=cmd_workflows_validate)

    p = wf_sub.add_parser("diff", help="Compare local JSON against live workflow")
    p.add_argument("id", help="Workflow ID to compare against")
    p.add_argument("file", help="Local JSON file path")
    p.set_defaults(func=cmd_workflows_diff)

    # ── executions ──
    ex = sub.add_parser("executions", aliases=["exec"], help="Execution operations")
    ex_sub = ex.add_subparsers(dest="exec_cmd")

    p = ex_sub.add_parser("list", aliases=["ls"], help="List executions")
    p.add_argument("--workflow-id", help="Filter by workflow ID")
    p.add_argument("--status", choices=["error", "success", "waiting", "running", "new"], help="Filter by status")
    p.add_argument("--limit", type=int, help="Max results")
    p.set_defaults(func=cmd_executions_list)

    p = ex_sub.add_parser("get", help="Get execution details")
    p.add_argument("id", help="Execution ID")
    p.set_defaults(func=cmd_executions_get)

    p = ex_sub.add_parser("retry", help="Retry a failed execution")
    p.add_argument("id", help="Execution ID")
    p.set_defaults(func=cmd_executions_retry)

    p = ex_sub.add_parser("delete", aliases=["rm"], help="Delete an execution")
    p.add_argument("id", help="Execution ID")
    p.set_defaults(func=cmd_executions_delete)

    p = ex_sub.add_parser("stop", help="Stop a running execution")
    p.add_argument("id", help="Execution ID")
    p.set_defaults(func=cmd_executions_stop)

    p = ex_sub.add_parser("tail", help="Watch executions in real time")
    p.add_argument("--workflow-id", help="Filter by workflow ID")
    p.add_argument(
        "--status",
        choices=["error", "success", "waiting", "running", "new"],
        help="Filter by status",
    )
    p.add_argument(
        "--interval", type=float, default=3.0,
        help="Poll interval in seconds (default: 3)",
    )
    p.set_defaults(func=cmd_executions_tail)

    # ── credentials ──
    cr = sub.add_parser("credentials", aliases=["creds"], help="Credential operations")
    cr_sub = cr.add_subparsers(dest="cred_cmd")

    p = cr_sub.add_parser("list", aliases=["ls"], help="List credentials")
    p.add_argument("--type", help="Filter by credential type")
    p.add_argument("--limit", type=int, help="Max results")
    p.set_defaults(func=cmd_credentials_list)

    p = cr_sub.add_parser("get", help="Get credential details")
    p.add_argument("id", help="Credential ID")
    p.set_defaults(func=cmd_credentials_get)

    p = cr_sub.add_parser("schema", help="Get schema for a credential type")
    p.add_argument("type_name", help="Credential type name")
    p.set_defaults(func=cmd_credentials_schema)

    p = cr_sub.add_parser("create", help="Create credential from JSON")
    p.add_argument("file", help="JSON file path")
    p.set_defaults(func=cmd_credentials_create)

    p = cr_sub.add_parser("delete", aliases=["rm"], help="Delete a credential")
    p.add_argument("id", help="Credential ID")
    p.set_defaults(func=cmd_credentials_delete)

    p = cr_sub.add_parser("transfer", help="Transfer credential to project")
    p.add_argument("id", help="Credential ID")
    p.add_argument("project_id", help="Destination project ID")
    p.set_defaults(func=cmd_credentials_transfer)

    # ── tags ──
    tg = sub.add_parser("tags", help="Tag operations")
    tg_sub = tg.add_subparsers(dest="tag_cmd")

    p = tg_sub.add_parser("list", aliases=["ls"], help="List tags")
    p.add_argument("--limit", type=int, help="Max results")
    p.set_defaults(func=cmd_tags_list)

    p = tg_sub.add_parser("create", help="Create a tag")
    p.add_argument("name", help="Tag name")
    p.set_defaults(func=cmd_tags_create)

    p = tg_sub.add_parser("get", help="Get a tag")
    p.add_argument("id", help="Tag ID")
    p.set_defaults(func=cmd_tags_get)

    p = tg_sub.add_parser("update", help="Rename a tag")
    p.add_argument("id", help="Tag ID")
    p.add_argument("name", help="New name")
    p.set_defaults(func=cmd_tags_update)

    p = tg_sub.add_parser("delete", aliases=["rm"], help="Delete a tag")
    p.add_argument("id", help="Tag ID")
    p.set_defaults(func=cmd_tags_delete)

    # ── variables ──
    vr = sub.add_parser("variables", aliases=["vars"], help="Variable operations")
    vr_sub = vr.add_subparsers(dest="var_cmd")

    p = vr_sub.add_parser("list", aliases=["ls"], help="List variables")
    p.add_argument("--limit", type=int, help="Max results")
    p.set_defaults(func=cmd_variables_list)

    p = vr_sub.add_parser("create", help="Create a variable")
    p.add_argument("key", help="Variable key")
    p.add_argument("value", help="Variable value")
    p.set_defaults(func=cmd_variables_create)

    p = vr_sub.add_parser("get", help="Get a variable")
    p.add_argument("id", help="Variable ID")
    p.set_defaults(func=cmd_variables_get)

    p = vr_sub.add_parser("update", help="Update a variable")
    p.add_argument("id", help="Variable ID")
    p.add_argument("--key", help="New key")
    p.add_argument("--value", help="New value")
    p.set_defaults(func=cmd_variables_update)

    p = vr_sub.add_parser("delete", aliases=["rm"], help="Delete a variable")
    p.add_argument("id", help="Variable ID")
    p.set_defaults(func=cmd_variables_delete)

    # ── projects ──
    pj = sub.add_parser("projects", help="Project operations")
    pj_sub = pj.add_subparsers(dest="proj_cmd")

    p = pj_sub.add_parser("list", aliases=["ls"], help="List projects")
    p.add_argument("--limit", type=int, help="Max results")
    p.set_defaults(func=cmd_projects_list)

    p = pj_sub.add_parser("get", help="Get a project")
    p.add_argument("id", help="Project ID")
    p.set_defaults(func=cmd_projects_get)

    p = pj_sub.add_parser("create", help="Create a project")
    p.add_argument("name", help="Project name")
    p.set_defaults(func=cmd_projects_create)

    p = pj_sub.add_parser("update", help="Update a project")
    p.add_argument("id", help="Project ID")
    p.add_argument("name", help="New name")
    p.set_defaults(func=cmd_projects_update)

    p = pj_sub.add_parser("delete", aliases=["rm"], help="Delete a project")
    p.add_argument("id", help="Project ID")
    p.set_defaults(func=cmd_projects_delete)

    p = pj_sub.add_parser("users", help="List users in a project")
    p.add_argument("id", help="Project ID")
    p.set_defaults(func=cmd_projects_users)

    # ── users ──
    us = sub.add_parser("users", help="User operations")
    us_sub = us.add_subparsers(dest="user_cmd")

    p = us_sub.add_parser("list", aliases=["ls"], help="List users")
    p.add_argument("--limit", type=int, help="Max results")
    p.set_defaults(func=cmd_users_list)

    p = us_sub.add_parser("get", help="Get a user")
    p.add_argument("id", help="User ID or email")
    p.set_defaults(func=cmd_users_get)

    p = us_sub.add_parser("delete", aliases=["rm"], help="Delete a user")
    p.add_argument("id", help="User ID")
    p.set_defaults(func=cmd_users_delete)

    p = us_sub.add_parser("change-role", help="Change a user's role")
    p.add_argument("id", help="User ID")
    p.add_argument("role", help="New role (e.g. global:member, global:admin)")
    p.set_defaults(func=cmd_users_change_role)

    # ── audit ──
    p = sub.add_parser("audit", help="Generate security audit")
    p.add_argument("--categories", help="Comma-separated: credentials,database,filesystem,instance,nodes")
    p.set_defaults(func=cmd_audit)

    # ── source-control ──
    sc = sub.add_parser("source-control", aliases=["sc"], help="Source control operations")
    sc_sub = sc.add_subparsers(dest="sc_cmd")

    p = sc_sub.add_parser("pull", help="Pull from source control")
    p.add_argument("--force", action="store_true", help="Force pull")
    p.set_defaults(func=cmd_source_control_pull)

    # ── community-packages ──
    pk = sub.add_parser("packages", aliases=["pkg"], help="Community package operations")
    pk_sub = pk.add_subparsers(dest="pkg_cmd")

    p = pk_sub.add_parser("list", aliases=["ls"], help="List installed packages")
    p.set_defaults(func=cmd_packages_list)

    p = pk_sub.add_parser("install", help="Install a package")
    p.add_argument("name", help="npm package name")
    p.set_defaults(func=cmd_packages_install)

    p = pk_sub.add_parser("get", help="Get package details")
    p.add_argument("name", help="Package name")
    p.set_defaults(func=cmd_packages_get)

    p = pk_sub.add_parser("update", help="Update a package")
    p.add_argument("name", help="Package name")
    p.set_defaults(func=cmd_packages_update)

    p = pk_sub.add_parser("uninstall", aliases=["rm"], help="Uninstall a package")
    p.add_argument("name", help="Package name")
    p.set_defaults(func=cmd_packages_uninstall)

    # ── nodes (local catalog -- no API needed) ──
    nd = sub.add_parser("nodes", help="Node catalog (local, auto-updating)")
    nd_sub = nd.add_subparsers(dest="node_cmd")

    p = nd_sub.add_parser("search", help="Search for nodes by keyword")
    p.add_argument("query", help="Search query")
    p.add_argument("--limit", type=int, default=20, help="Max results")
    p.set_defaults(func=cmd_nodes_search)

    p = nd_sub.add_parser("get", help="Get node details")
    p.add_argument("name", help="Node name (e.g. slack, httpRequest)")
    p.add_argument("--full", action="store_true", help="Show full property schema")
    p.set_defaults(func=cmd_nodes_get)

    p = nd_sub.add_parser("list", aliases=["ls"], help="List all nodes")
    p.add_argument("--group", help="Filter by group (trigger, input, output, transform)")
    p.add_argument("--category", help="Filter by category")
    p.add_argument("--credential", help="Filter by credential type")
    p.add_argument("--ai-tools", action="store_true", help="Only AI-usable tool nodes")
    p.add_argument("--limit", type=int, help="Max results")
    p.set_defaults(func=cmd_nodes_list)

    p = nd_sub.add_parser("update", help="Force-update node catalog from npm")
    p.set_defaults(func=cmd_nodes_update)

    p = nd_sub.add_parser("info", help="Show catalog version info")
    p.set_defaults(func=cmd_nodes_info)

    # ── webhooks ──
    wh = sub.add_parser("webhooks", aliases=["wh"], help="Webhook operations")
    wh_sub = wh.add_subparsers(dest="wh_cmd")

    p = wh_sub.add_parser("test", help="Send test payload to a webhook workflow")
    p.add_argument("workflow_id", help="Workflow ID")
    p.add_argument("--data", help="JSON payload (e.g. '{\"key\": \"value\"}')")
    p.add_argument("--method", default="POST", choices=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"], help="HTTP method (default: POST)")
    p.set_defaults(func=cmd_webhooks_test)

    p = wh_sub.add_parser("list", aliases=["ls"], help="List webhook URLs from active workflows")
    p.set_defaults(func=cmd_webhooks_list)

    # ── skills (Claude Code) ──
    sk = sub.add_parser(
        "skills",
        help="Manage bundled Claude Code skills",
        description="Install, list, and uninstall the Claude Code skills bundled with n8n-cli.",
    )
    sk_sub = sk.add_subparsers(dest="skills_cmd")

    p = sk_sub.add_parser("list", aliases=["ls"], help="List bundled skills and installation status")
    p.set_defaults(func=cmd_skills_list)

    p = sk_sub.add_parser("install", help="Install bundled skills into ~/.claude/skills/")
    p.add_argument("names", nargs="*", help="Specific skill names (omit to install all)")
    p.add_argument("--force", action="store_true", help="Overwrite existing installed skills")
    p.set_defaults(func=cmd_skills_install)

    p = sk_sub.add_parser("uninstall", aliases=["rm"], help="Remove installed skills")
    p.add_argument("names", nargs="+", help="Skill names to remove")
    p.set_defaults(func=cmd_skills_uninstall)

    p = sk_sub.add_parser("path", help="Print the install target directory")
    p.set_defaults(func=cmd_skills_path)

    p = sk_sub.add_parser(
        "doctor",
        help="Validate every bundled SKILL.md against the live CLI surface",
    )
    p.set_defaults(func=cmd_skills_doctor)

    # ── open (browser) ──
    op = sub.add_parser(
        "open",
        help="Open n8n web UI in the browser",
        description="Open the n8n editor, a specific workflow, or settings in your browser.",
    )
    op.add_argument(
        "target", nargs="?", default=None,
        choices=["workflow", "execution", "settings", "credentials"],
        help="What to open (default: editor home)",
    )
    op.add_argument("target_id", nargs="?", default=None, help="ID for workflow or execution")
    op.set_defaults(func=cmd_open)

    # ── completion ──
    cp = sub.add_parser(
        "completion",
        help="Print shell completion script",
        description="Generate a shell completion script for bash or zsh.",
    )
    cp.add_argument(
        "shell", choices=["bash", "zsh"],
        help="Shell type (bash or zsh)",
    )
    cp.set_defaults(func=cmd_completion)

    # ── api (raw escape hatch) ──
    ap = sub.add_parser(
        "api",
        help="Raw API call to any n8n REST endpoint",
        description=(
            "Send a raw HTTP request to the n8n REST API. "
            "Use this for endpoints the CLI doesn't cover yet."
        ),
    )
    ap.add_argument("path", help="API path (e.g. /workflows, /executions/123)")
    ap.add_argument(
        "-X", "--method", default="GET",
        choices=["GET", "POST", "PUT", "PATCH", "DELETE"],
        help="HTTP method (default: GET)",
    )
    ap.add_argument("-d", "--data", help="JSON request body (inline string)")
    ap.add_argument("--data-file", help="JSON request body (read from file)")
    ap.set_defaults(func=cmd_api)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    func = getattr(args, "func", None)
    if not func:
        # Subcommand group with no sub-subcommand
        parser.parse_args([args.command, "--help"])
        sys.exit(0)

    try:
        func(args)
    except N8nApiError as e:
        error_data = {
            "error": True,
            "type": "N8nApiError",
            "status": e.status,
            "message": e.message,
        }
        if e.recovery_hint:
            error_data["recovery_hint"] = e.recovery_hint
        if _json(args):
            print(json.dumps(error_data, indent=2), file=sys.stderr)
        else:
            print(f"Error: HTTP {e.status}: {e.message}", file=sys.stderr)
            if e.recovery_hint:
                print(f"Hint:  {e.recovery_hint}", file=sys.stderr)
        sys.exit(1)
    except N8nError as e:
        error_data = {
            "error": True,
            "type": type(e).__name__,
            "message": str(e),
        }
        if e.recovery_hint:
            error_data["recovery_hint"] = e.recovery_hint
        if _json(args):
            print(json.dumps(error_data, indent=2), file=sys.stderr)
        else:
            print(f"Error: {e}", file=sys.stderr)
            if e.recovery_hint:
                print(f"Hint:  {e.recovery_hint}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"Error: File not found: {e}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    main()
