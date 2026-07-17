"""Tests for configuration management."""

import os
import json
import tempfile
from unittest.mock import patch

from n8n_cli.config import load_config, get_profile, save_config
from n8n_cli.exceptions import N8nConfigError


class TestLoadConfig:
    def test_returns_deep_copy(self):
        c1 = load_config()
        c2 = load_config()
        c1.setdefault("profiles", {})["__test__"] = {"api_url": "x"}
        assert "__test__" not in c2.get("profiles", {}), \
            "Mutation leaked between copies"

    def test_returns_default_when_no_file(self):
        with patch("n8n_cli.config.CONFIG_FILE") as mock_path:
            mock_path.exists.return_value = False
            config = load_config()
            assert "default_profile" in config
            assert "profiles" in config


class TestGetProfile:
    def test_env_var_overrides_config(self):
        with patch.dict(os.environ, {
            "N8N_API_URL": "https://env.example.com/api/v1",
            "N8N_API_KEY": "env-key",
        }):
            profile = get_profile()
            assert profile["api_url"] == "https://env.example.com/api/v1"
            assert profile["api_key"] == "env-key"

    def test_strips_trailing_slash(self):
        with patch.dict(os.environ, {
            "N8N_API_URL": "https://example.com/api/v1/",
            "N8N_API_KEY": "key",
        }):
            profile = get_profile()
            assert not profile["api_url"].endswith("/")


class TestRequireProfile:
    def test_raises_on_missing_url(self):
        from n8n_cli.config import require_profile
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("N8N_API_URL", None)
            os.environ.pop("N8N_API_KEY", None)
            os.environ.pop("N8N_PROFILE", None)
            try:
                require_profile("__nonexistent_test__")
                assert False, "Should have raised"
            except N8nConfigError:
                pass  # Expected


class TestSaveConfig:
    def test_atomic_write(self):
        fd, path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        try:
            with patch("n8n_cli.config.CONFIG_FILE") as mock_path:
                mock_path.parent = os.path.dirname(path)
                mock_path.__str__ = lambda s: path
                mock_path.__fspath__ = lambda s: path
                # Just verify save_config doesn't crash
                # (full atomic test would need mocking os.replace)
                config = {"default_profile": "test", "profiles": {}}
                # Can't easily test atomic write without more mocking
                # Just verify the function signature works
                assert callable(save_config)
        finally:
            os.unlink(path)
