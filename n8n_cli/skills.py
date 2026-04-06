"""Bundled Claude Code skills — list, install, uninstall.

Skills live in `n8n_cli/skills_data/<skill-name>/SKILL.md` and ship inside the
wheel as package data. They get installed into the user's Claude Code skills
directory (default: `~/.claude/skills/`) where Claude Code auto-discovers them.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path
from typing import Iterable

# importlib.resources.files is the supported, package-data-aware way to read
# files shipped with a Python package. Works for editable, wheel, and sdist
# installs alike. Requires Python 3.9+ (matches our pyproject requires-python).
from importlib.resources import files as _pkg_files


SKILLS_PACKAGE = "n8n_cli.skills_data"
SKILL_FILENAME = "SKILL.md"
DEFAULT_INSTALL_DIR = Path.home() / ".claude" / "skills"


# ── Discovery ────────────────────────────────────────────────────────

def _bundled_root():
    """Traversable handle for the bundled skills_data package."""
    return _pkg_files(SKILLS_PACKAGE)


def list_bundled_skill_names() -> list[str]:
    """Return sorted names of all bundled skills."""
    root = _bundled_root()
    names = []
    for entry in root.iterdir():
        # Each skill is a directory containing SKILL.md
        if entry.is_dir() and (entry / SKILL_FILENAME).is_file():
            names.append(entry.name)
    return sorted(names)


def read_skill_metadata(name: str) -> dict:
    """Parse the YAML-ish frontmatter of a bundled skill's SKILL.md."""
    skill_file = _bundled_root() / name / SKILL_FILENAME
    if not skill_file.is_file():
        raise FileNotFoundError(f"Bundled skill not found: {name}")
    text = skill_file.read_text(encoding="utf-8")

    meta: dict = {"name": name}
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            block = text[3:end]
            for line in block.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if ":" not in line:
                    continue
                key, _, value = line.partition(":")
                value = value.strip().strip('"').strip("'")
                meta[key.strip()] = value
    return meta


# ── Install dir resolution ──────────────────────────────────────────

def install_dir() -> Path:
    """Resolve the target install dir for Claude Code skills.

    Honors $CLAUDE_SKILLS_DIR if set, otherwise defaults to ~/.claude/skills.
    """
    override = os.environ.get("CLAUDE_SKILLS_DIR")
    if override:
        return Path(override).expanduser()
    return DEFAULT_INSTALL_DIR


def _is_installed(name: str, target_dir: Path) -> bool:
    return (target_dir / name / SKILL_FILENAME).is_file()


# ── Copy logic ───────────────────────────────────────────────────────

def _copy_skill_tree(name: str, target_dir: Path) -> int:
    """Copy a single bundled skill directory into target_dir/<name>/.

    Returns the number of files written. Raises FileNotFoundError if the
    bundled skill doesn't exist.
    """
    src_root = _bundled_root() / name
    if not src_root.is_dir():
        raise FileNotFoundError(f"Bundled skill not found: {name}")

    dest = target_dir / name
    dest.mkdir(parents=True, exist_ok=True)
    written = 0

    # Walk every file in the bundled skill directory (in case future skills
    # ship more than just SKILL.md — e.g. helper scripts, prompts, examples).
    for entry in src_root.iterdir():
        if entry.is_file():
            with entry.open("rb") as fp:
                data = fp.read()
            (dest / entry.name).write_bytes(data)
            written += 1
        elif entry.is_dir():
            # Recursively copy subdirectories. importlib.resources Traversables
            # don't support shutil.copytree directly, so we walk manually.
            written += _copy_subtree(entry, dest / entry.name)
    return written


def _copy_subtree(src, dest: Path) -> int:
    dest.mkdir(parents=True, exist_ok=True)
    written = 0
    for entry in src.iterdir():
        if entry.is_file():
            (dest / entry.name).write_bytes(entry.read_bytes())
            written += 1
        elif entry.is_dir():
            written += _copy_subtree(entry, dest / entry.name)
    return written


# ── Public commands (called from cli.py) ────────────────────────────

def cmd_list(as_json: bool = False) -> None:
    target = install_dir()
    rows = []
    for name in list_bundled_skill_names():
        meta = read_skill_metadata(name)
        rows.append({
            "name": name,
            "description": meta.get("description", ""),
            "installed": _is_installed(name, target),
        })

    if as_json:
        print(json.dumps({"install_dir": str(target), "skills": rows}, indent=2))
        return

    print(f"Install target: {target}")
    print(f"Bundled skills: {len(rows)}")
    print()
    name_width = max(len(r["name"]) for r in rows)
    for r in rows:
        marker = "[installed]" if r["installed"] else "[          ]"
        print(f"  {marker}  {r['name']:<{name_width}}  {r['description']}")
    print()
    print("Install all:        n8n-cli skills install")
    print("Install one:        n8n-cli skills install <name>")
    print("Force overwrite:    n8n-cli skills install --force")


def cmd_install(
    names: Iterable[str] | None = None,
    force: bool = False,
    as_json: bool = False,
) -> None:
    target = install_dir()
    target.mkdir(parents=True, exist_ok=True)

    bundled = list_bundled_skill_names()
    if not names:
        to_install = bundled
    else:
        to_install = []
        for n in names:
            if n not in bundled:
                msg = f"Unknown skill: {n}. Run `n8n-cli skills list` to see available skills."
                if as_json:
                    print(json.dumps({"error": msg}, indent=2), file=sys.stderr)
                else:
                    print(f"Error: {msg}", file=sys.stderr)
                sys.exit(1)
            to_install.append(n)

    results = []
    for name in to_install:
        already = _is_installed(name, target)
        if already and not force:
            results.append({"name": name, "status": "skipped", "reason": "already installed (use --force to overwrite)"})
            continue
        files_written = _copy_skill_tree(name, target)
        results.append({
            "name": name,
            "status": "overwritten" if already else "installed",
            "files": files_written,
            "path": str(target / name),
        })

    if as_json:
        print(json.dumps({"install_dir": str(target), "results": results}, indent=2))
        return

    print(f"Install target: {target}")
    print()
    for r in results:
        if r["status"] == "skipped":
            print(f"  - {r['name']:<24}  skipped  ({r['reason']})")
        else:
            verb = "overwrote" if r["status"] == "overwritten" else "installed"
            print(f"  ✓ {r['name']:<24}  {verb}  ({r['files']} file{'s' if r['files'] != 1 else ''})")
    installed_count = sum(1 for r in results if r["status"] != "skipped")
    skipped_count = sum(1 for r in results if r["status"] == "skipped")
    print()
    print(f"Done. {installed_count} installed, {skipped_count} skipped.")
    if installed_count:
        print("Restart Claude Code (or open a new session) to pick up the new skills.")


def cmd_uninstall(names: Iterable[str], as_json: bool = False) -> None:
    target = install_dir()
    results = []
    for name in names:
        skill_dir = target / name
        if not skill_dir.is_dir():
            results.append({"name": name, "status": "not_installed"})
            continue
        # Safety check: only remove dirs that look like skill dirs (have SKILL.md)
        if not (skill_dir / SKILL_FILENAME).is_file():
            results.append({"name": name, "status": "skipped", "reason": "no SKILL.md found, refusing to delete"})
            continue
        shutil.rmtree(skill_dir)
        results.append({"name": name, "status": "removed", "path": str(skill_dir)})

    if as_json:
        print(json.dumps({"install_dir": str(target), "results": results}, indent=2))
        return

    for r in results:
        if r["status"] == "removed":
            print(f"  ✓ removed       {r['name']}")
        elif r["status"] == "not_installed":
            print(f"  - {r['name']}: not installed")
        else:
            print(f"  - {r['name']}: {r.get('reason', r['status'])}")


def cmd_path(as_json: bool = False) -> None:
    target = install_dir()
    if as_json:
        print(json.dumps({"install_dir": str(target), "exists": target.is_dir()}, indent=2))
    else:
        print(target)


# ── Doctor ───────────────────────────────────────────────────────────

def cmd_doctor(as_json: bool = False) -> None:
    """Validate every bundled SKILL.md against the live CLI surface.

    For each skill, extract every `n8n-cli ...` invocation and check that
    the subcommand path and flags reference real CLI commands. Catches
    typos, drift between docs and code, and copy-paste mistakes in
    user-authored skills.
    """
    import argparse as _argparse
    import re as _re
    from . import cli as _cli_mod

    # Walk the parser to collect every leaf command path → set of valid flags
    def _collect(parser, prefix="", out=None):
        if out is None:
            out = {}
        for action in parser._actions:
            if isinstance(action, _argparse._SubParsersAction):
                for name, sub in action.choices.items():
                    path = f"{prefix} {name}".strip()
                    has_subs = any(
                        isinstance(a, _argparse._SubParsersAction) for a in sub._actions
                    )
                    if has_subs:
                        _collect(sub, path, out)
                    else:
                        flags = set()
                        for sa in sub._actions:
                            if isinstance(sa, _argparse._SubParsersAction):
                                continue
                            for opt in sa.option_strings:
                                if opt not in ("-h", "--help"):
                                    flags.add(opt)
                        out[path] = flags
        return out

    leafs = _collect(_cli_mod.build_parser())
    global_flags = {"-p", "--profile", "--json", "-v", "--version", "-h", "--help"}
    top_groups = {
        "health", "discover", "config", "workflows", "wf", "executions",
        "exec", "credentials", "creds", "tags", "variables", "vars",
        "projects", "users", "audit", "source-control", "sc", "packages",
        "pkg", "nodes", "webhooks", "wh", "skills",
    }

    def _parse_invocation(line):
        line = line.strip().strip("`").strip("$").strip()
        if not line.startswith("n8n-cli"):
            return None, []
        parts = line.split()[1:]
        cleaned = []
        skip_next = False
        for tok in parts:
            if skip_next:
                skip_next = False
                continue
            if tok in ("-p", "--profile"):
                skip_next = True
                continue
            if tok in global_flags or tok.startswith("--profile="):
                continue
            cleaned.append(tok)
        if not cleaned or cleaned[0] not in top_groups:
            return None, []
        for n in range(min(3, len(cleaned)), 0, -1):
            candidate = " ".join(cleaned[:n])
            if candidate in leafs:
                rest = cleaned[n:]
                used_flags = []
                for t in rest:
                    if t.startswith("--"):
                        used_flags.append(t.split("=")[0])
                    elif t.startswith("-") and len(t) > 1 and not t[1:].isdigit():
                        used_flags.append(t)
                return candidate, used_flags
        return None, []

    # Walk every bundled skill and check it
    bundled_root = _bundled_root()
    skill_results = []
    for entry in sorted(bundled_root.iterdir(), key=lambda e: e.name):
        if not entry.is_dir():
            continue
        skill_file = entry / SKILL_FILENAME
        if not skill_file.is_file():
            continue
        text = skill_file.read_text(encoding="utf-8")
        bad_cmds = []
        bad_flags = []
        invocation_count = 0
        for ln, line in enumerate(text.splitlines(), 1):
            if "n8n-cli" not in line:
                continue
            for m in _re.finditer(r"`?(n8n-cli[^`\n]*)`?", line):
                inv = m.group(1).rstrip("`").rstrip()
                inv = _re.split(r"[.,;:)]", inv)[0]
                cmd, flags_used = _parse_invocation(inv)
                tokens = inv.split()[1:]
                tc = [
                    t for t in tokens
                    if not t.startswith("-")
                    and t not in ("--profile", "--json", "-p", "-v")
                ]
                if not tc or tc[0] not in top_groups:
                    continue
                invocation_count += 1
                if cmd is None:
                    bad_cmds.append({"line": ln, "invocation": inv})
                    continue
                valid_flags = leafs.get(cmd, set())
                for f in flags_used:
                    if f not in valid_flags and f not in global_flags:
                        bad_flags.append({"line": ln, "command": cmd, "flag": f, "invocation": inv})
        skill_results.append({
            "name": entry.name,
            "invocations_checked": invocation_count,
            "bad_commands": bad_cmds,
            "bad_flags": bad_flags,
            "ok": not bad_cmds and not bad_flags,
        })

    total = len(skill_results)
    passing = sum(1 for r in skill_results if r["ok"])
    failing = total - passing

    if as_json:
        print(json.dumps({
            "total": total,
            "passing": passing,
            "failing": failing,
            "results": skill_results,
        }, indent=2))
        return

    print(f"Skills doctor — checked {total} bundled skills")
    print(f"  Passing: {passing}")
    print(f"  Failing: {failing}")
    print()
    if failing == 0:
        print("✅ All skills reference only valid n8n-cli commands and flags.")
        return
    for r in skill_results:
        if r["ok"]:
            continue
        print(f"❌ {r['name']}")
        for b in r["bad_commands"]:
            print(f"    line {b['line']}: unknown command in: {b['invocation']}")
        for b in r["bad_flags"]:
            print(f"    line {b['line']}: command `{b['command']}` uses unknown flag `{b['flag']}`")
            print(f"      in: {b['invocation']}")
        print()
    sys.exit(1)
