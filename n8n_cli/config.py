"""Configuration management for n8n-cli.

Reads from ~/.n8n-cli.json or environment variables.
Supports multiple named profiles for different n8n instances.
"""

import json
import os
import sys
from pathlib import Path
from typing import Optional

CONFIG_FILE = Path.home() / ".n8n-cli.json"

DEFAULT_CONFIG = {
    "default_profile": "default",
    "profiles": {
        "default": {
            "api_url": "",
            "api_key": "",
        }
    },
}


def load_config() -> dict:
    """Load config file, creating default if missing."""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            return json.load(f)
    import copy
    return copy.deepcopy(DEFAULT_CONFIG)


def save_config(config: dict) -> None:
    """Write config to disk atomically with secure permissions."""
    import tempfile
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=CONFIG_FILE.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(config, f, indent=2)
        os.chmod(tmp_path, 0o600)
        os.replace(tmp_path, CONFIG_FILE)
    except Exception:
        os.unlink(tmp_path)
        raise


def get_profile(profile_name: Optional[str] = None) -> dict:
    """Resolve the active profile, with env-var overrides.

    Priority order:
    1. Environment variables (N8N_API_URL, N8N_API_KEY)
    2. Named profile from config file
    3. default profile from config file
    """
    config = load_config()

    name = profile_name or os.environ.get("N8N_PROFILE") or config.get("default_profile", "default")
    profiles = config.get("profiles", {})
    profile = profiles.get(name, {})

    api_url = os.environ.get("N8N_API_URL") or profile.get("api_url", "")
    api_key = os.environ.get("N8N_API_KEY") or profile.get("api_key", "")

    if not api_url:
        return {"api_url": "", "api_key": "", "profile_name": name}

    # Normalize: strip trailing slash
    api_url = api_url.rstrip("/")

    return {
        "api_url": api_url,
        "api_key": api_key,
        "profile_name": name,
    }


def require_profile(profile_name: Optional[str] = None) -> dict:
    """Get profile or exit with error if not configured."""
    p = get_profile(profile_name)
    if not p["api_url"]:
        print("Error: n8n API URL not configured.", file=sys.stderr)
        print("Set N8N_API_URL env var or run: n8n-cli config set-profile <name> --url <url> --key <key>", file=sys.stderr)
        sys.exit(1)
    if not p["api_key"]:
        print("Error: n8n API key not configured.", file=sys.stderr)
        print("Set N8N_API_KEY env var or run: n8n-cli config set-profile <name> --url <url> --key <key>", file=sys.stderr)
        sys.exit(1)
    return p
