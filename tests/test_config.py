import os
import unittest
from unittest.mock import patch

from n8n_cli import config

CFG = {
    "default_profile": "cloud",
    "profiles": {
        "cloud": {"api_url": "https://cloud.example/api/v1", "api_key": "cloudkey"},
        "hostinger": {"api_url": "https://host.example/api/v1/", "api_key": "hostkey"},
    },
}


class ProfilePrecedenceTest(unittest.TestCase):
    def run_get(self, env, name=None):
        with patch.object(config, "load_config", return_value=CFG), \
                patch.dict(os.environ, env, clear=True):
            return config.get_profile(name)

    def test_explicit_profile_beats_env_key(self):
        p = self.run_get({"N8N_API_KEY": "envkey", "N8N_API_URL": "https://env.example"}, "hostinger")
        self.assertEqual(p["api_key"], "hostkey")
        self.assertEqual(p["api_url"], "https://host.example/api/v1")

    def test_env_applies_without_explicit_profile(self):
        p = self.run_get({"N8N_API_KEY": "envkey"})
        self.assertEqual(p["api_key"], "envkey")
        self.assertEqual(p["api_url"], "https://cloud.example/api/v1")

    def test_env_fills_gap_in_explicit_profile(self):
        cfg = {"profiles": {"x": {"api_url": "https://x.example"}}}
        with patch.object(config, "load_config", return_value=cfg), \
                patch.dict(os.environ, {"N8N_API_KEY": "envkey"}, clear=True):
            self.assertEqual(config.get_profile("x")["api_key"], "envkey")


if __name__ == "__main__":
    unittest.main()
