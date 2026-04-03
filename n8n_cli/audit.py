"""Audit operations for n8n-cli."""

import json
from typing import Optional

from .client import N8nClient


def generate_audit(
    client: N8nClient,
    categories: Optional[str] = None,
    as_json: bool = False,
) -> None:
    """Generate a security audit report.

    Categories: credentials, database, filesystem, instance, nodes
    """
    body = {}
    if categories:
        body["additionalOptions"] = {"categories": categories.split(",")}

    result = client.post("/audit", body=body if body else None)

    if as_json:
        print(json.dumps(result, indent=2))
        return

    if not result:
        print("Audit completed with no findings.")
        return

    # Parse audit results
    if isinstance(result, dict):
        for category, findings in result.items():
            if isinstance(findings, list) and findings:
                print(f"\n## {category}")
                print("-" * 40)
                for finding in findings:
                    if isinstance(finding, dict):
                        risk = finding.get("risk", "unknown")
                        msg = finding.get("message", finding.get("description", ""))
                        print(f"  [{risk.upper()}] {msg}")
                    else:
                        print(f"  {finding}")
    else:
        print(json.dumps(result, indent=2))
