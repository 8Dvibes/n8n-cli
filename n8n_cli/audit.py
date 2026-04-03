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

    # n8n returns: {"Category Risk Report": {risk, sections: [{title, description, location: [...]}]}}
    if isinstance(result, dict):
        finding_count = 0
        for report_name, report in result.items():
            if isinstance(report, dict):
                risk = report.get("risk", "unknown")
                sections = report.get("sections", [])
                if sections:
                    print(f"\n## {report_name}")
                    print("-" * 50)
                    for section in sections:
                        title = section.get("title", "")
                        desc = section.get("description", "")
                        locations = section.get("location", [])
                        count = len(locations) if isinstance(locations, list) else 0
                        finding_count += count
                        print(f"\n  {title} ({count} finding{'s' if count != 1 else ''})")
                        if desc:
                            print(f"  {desc}")
                        if isinstance(locations, list):
                            for loc in locations[:10]:
                                if isinstance(loc, dict):
                                    name = loc.get("name", loc.get("id", ""))
                                    kind = loc.get("kind", loc.get("type", ""))
                                    print(f"    - {name}" + (f" ({kind})" if kind else ""))
                                else:
                                    print(f"    - {loc}")
                            if count > 10:
                                print(f"    ... and {count - 10} more")
            elif isinstance(report, list) and report:
                print(f"\n## {report_name}")
                print("-" * 50)
                for item in report:
                    if isinstance(item, dict):
                        risk = item.get("risk", "unknown")
                        msg = item.get("message", item.get("description", ""))
                        print(f"  [{risk.upper()}] {msg}")
                        finding_count += 1
                    else:
                        print(f"  {item}")
                        finding_count += 1

        print(f"\nTotal findings: {finding_count}")
    else:
        print(json.dumps(result, indent=2))
