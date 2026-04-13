"""Execution operations for n8n-cli."""

import json
import sys
import time
from typing import Optional

from .client import N8nClient


def list_executions(
    client: N8nClient,
    workflow_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: Optional[int] = None,
    as_json: bool = False,
) -> None:
    """List executions with optional filters."""
    params = {}
    if workflow_id:
        params["workflowId"] = workflow_id
    if status:
        params["status"] = status

    if limit is not None:
        execs = client.paginate("/executions", params=params, limit=limit)
    else:
        execs = client.paginate("/executions", params=params)

    if as_json:
        print(json.dumps(execs, indent=2))
        return

    if not execs:
        print("No executions found.")
        return

    print(f"{'ID':<14} {'Status':<12} {'Workflow':<20} {'Started':<22} {'Duration'}")
    print("-" * 85)
    for ex in execs:
        eid = str(ex.get("id", ""))
        st = ex.get("status", "unknown")
        wf_name = ""
        wf_data = ex.get("workflowData") or ex.get("workflowName")
        if isinstance(wf_data, dict):
            wf_name = wf_data.get("name", "")[:18]
        elif isinstance(wf_data, str):
            wf_name = wf_data[:18]

        started = (ex.get("startedAt") or "")[:19]

        # Calculate duration
        duration = ""
        if ex.get("startedAt") and ex.get("stoppedAt"):
            try:
                from datetime import datetime
                s = ex["startedAt"][:19]
                e = ex["stoppedAt"][:19]
                start_dt = datetime.fromisoformat(s)
                end_dt = datetime.fromisoformat(e)
                delta = end_dt - start_dt
                secs = delta.total_seconds()
                if secs < 60:
                    duration = f"{secs:.1f}s"
                else:
                    duration = f"{secs/60:.1f}m"
            except Exception:
                duration = ""

        print(f"{eid:<14} {st:<12} {wf_name:<20} {started:<22} {duration}")

    print(f"\nTotal: {len(execs)} execution(s)")


def get_execution(client: N8nClient, execution_id: str, as_json: bool = False) -> None:
    """Get a single execution by ID."""
    ex = client.get(f"/executions/{execution_id}")

    if as_json:
        print(json.dumps(ex, indent=2))
        return

    print(f"ID:         {ex.get('id')}")
    print(f"Status:     {ex.get('status')}")
    print(f"Mode:       {ex.get('mode', 'N/A')}")
    print(f"Started:    {ex.get('startedAt', 'N/A')}")
    print(f"Stopped:    {ex.get('stoppedAt', 'N/A')}")
    print(f"Finished:   {ex.get('finished', 'N/A')}")

    wf = ex.get("workflowData") or {}
    wf_id = ex.get("workflowId") or (wf.get("id") if isinstance(wf, dict) else None) or "N/A"
    wf_name = wf.get("name", "N/A") if isinstance(wf, dict) else "N/A"
    print(f"Workflow:   {wf_name} (ID: {wf_id})")

    # Show error details if failed
    data = ex.get("data", {})
    if isinstance(data, dict):
        result = data.get("resultData", {})
        error = result.get("error")
        if error:
            print(f"\nError:")
            if isinstance(error, dict):
                print(f"  Message:  {error.get('message', '')}")
                print(f"  Node:     {error.get('node', {}).get('name', 'N/A') if isinstance(error.get('node'), dict) else error.get('node', 'N/A')}")
                if error.get("stack"):
                    # Just first 3 lines of stack
                    stack_lines = str(error["stack"]).split("\n")[:3]
                    print(f"  Stack:    {stack_lines[0]}")
                    for line in stack_lines[1:]:
                        print(f"            {line}")
            else:
                print(f"  {error}")

        # Show per-node run data summary
        run_data = result.get("runData", {})
        if run_data:
            print(f"\nNode Results:")
            for node_name, runs in run_data.items():
                if isinstance(runs, list) and runs:
                    last = runs[-1]
                    if isinstance(last, dict):
                        node_error = last.get("error")
                        status = "ERROR" if node_error else "OK"
                        items = 0
                        main = last.get("data", {}).get("main", [])
                        if isinstance(main, list) and main:
                            first = main[0]
                            if isinstance(first, list):
                                items = len(first)
                        print(f"  {node_name}: {status} ({items} items)")


def retry_execution(client: N8nClient, execution_id: str, as_json: bool = False) -> None:
    """Retry a failed execution."""
    result = client.post(f"/executions/{execution_id}/retry")

    if as_json:
        print(json.dumps(result, indent=2))
        return

    if isinstance(result, dict):
        print(f"Retry started. New execution: {result.get('id', 'pending')}")
    else:
        print(f"Retry queued for execution {execution_id}")


def delete_execution(client: N8nClient, execution_id: str, as_json: bool = False) -> None:
    """Delete an execution."""
    result = client.delete(f"/executions/{execution_id}")

    if as_json:
        print(json.dumps(result, indent=2) if result else '{"deleted": true}')
        return

    print(f"Deleted execution: {execution_id}")


def stop_execution(client: N8nClient, execution_id: str, as_json: bool = False) -> None:
    """Stop a running execution."""
    result = client.post(f"/executions/{execution_id}/stop")

    if as_json:
        print(json.dumps(result, indent=2))
        return

    print(f"Stopped execution: {execution_id}")


def tail_executions(
    client: N8nClient,
    workflow_id: Optional[str] = None,
    status: Optional[str] = None,
    interval: float = 3.0,
    as_json: bool = False,
) -> None:
    """Watch executions in real time by polling the API.

    Prints new executions as they appear, similar to `stripe logs tail`
    or `wrangler tail`. Polls every `interval` seconds.

    Press Ctrl+C to stop.
    """
    seen_ids: set = set()

    # Seed with recent executions so we don't replay history
    params = {}
    if workflow_id:
        params["workflowId"] = workflow_id
    if status:
        params["status"] = status

    try:
        initial = client.paginate("/executions", params=params, limit=10)
        for ex in initial:
            seen_ids.add(str(ex.get("id", "")))
    except Exception:
        pass  # If initial fetch fails, start fresh

    if not as_json:
        print("Watching executions... (Ctrl+C to stop)", file=sys.stderr)
        if workflow_id:
            print(f"  Filtering: workflow {workflow_id}", file=sys.stderr)
        if status:
            print(f"  Filtering: status {status}", file=sys.stderr)
        print(file=sys.stderr)

    try:
        while True:
            try:
                recent = client.paginate(
                    "/executions", params=params, limit=20
                )
            except Exception as poll_err:
                print(
                    f"  ! Poll failed: {poll_err} (retrying...)",
                    file=sys.stderr,
                )
                time.sleep(interval)
                continue

            new_execs = []
            for ex in recent:
                eid = str(ex.get("id", ""))
                if eid and eid not in seen_ids:
                    seen_ids.add(eid)
                    new_execs.append(ex)

            for ex in reversed(new_execs):  # Oldest first
                if as_json:
                    print(json.dumps({
                        "id": ex.get("id"),
                        "status": ex.get("status"),
                        "mode": ex.get("mode"),
                        "startedAt": ex.get("startedAt"),
                        "stoppedAt": ex.get("stoppedAt"),
                        "workflowId": ex.get("workflowId"),
                        "workflowName": (
                            ex.get("workflowData", {}).get("name")
                            if isinstance(ex.get("workflowData"), dict)
                            else ex.get("workflowName")
                        ),
                    }))
                    sys.stdout.flush()
                else:
                    eid = str(ex.get("id", ""))
                    st = ex.get("status", "?")
                    started = (ex.get("startedAt") or "")[:19]
                    wf_data = ex.get("workflowData") or {}
                    wf_name = (
                        wf_data.get("name", "")
                        if isinstance(wf_data, dict)
                        else str(wf_data)
                    )[:30]

                    # Color-code status
                    marker = "+"
                    if st == "error":
                        marker = "X"
                    elif st == "success":
                        marker = "+"
                    elif st in ("running", "waiting"):
                        marker = "~"

                    print(
                        f"  {marker} [{started}] "
                        f"{st:<10} {eid:<14} {wf_name}"
                    )
                    sys.stdout.flush()

            time.sleep(interval)

    except KeyboardInterrupt:
        if not as_json:
            print("\nStopped.", file=sys.stderr)


def get_execution_tags(client: N8nClient, execution_id: str, as_json: bool = False) -> None:
    """Get tags for an execution (n8n 1.x+)."""
    result = client.get(f"/executions/{execution_id}/tags")
    if as_json:
        print(json.dumps(result, indent=2))
        return
    tags = result if isinstance(result, list) else result.get("data", [])
    if not tags:
        print(f"No tags on execution {execution_id}")
        return
    for t in tags:
        print(f"  {t.get('id', '')}  {t.get('name', '')}")
