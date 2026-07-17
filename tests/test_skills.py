"""Tests for the bundled skills system."""

from n8n_cli.skills import list_bundled_skill_names, read_skill_metadata


class TestSkillDiscovery:
    def test_finds_expected_count(self):
        names = list_bundled_skill_names()
        assert len(names) >= 30, f"Only found {len(names)} skills, expected >= 30"

    def test_known_skills_present(self):
        names = list_bundled_skill_names()
        for expected in ["n8n-cli-status", "n8n-cli-debug", "n8n-cli-backup", "n8n-cli-smoke"]:
            assert expected in names, f"Missing skill: {expected}"


class TestSkillMetadata:
    def test_parses_name(self):
        meta = read_skill_metadata("n8n-cli-status")
        assert meta.get("name"), "No name in metadata"

    def test_parses_description(self):
        meta = read_skill_metadata("n8n-cli-status")
        assert meta.get("description"), "No description in metadata"
        assert len(meta["description"]) > 10

    def test_parses_user_invocable(self):
        meta = read_skill_metadata("n8n-cli-status")
        assert meta.get("user_invocable") == "true"

    def test_unknown_skill_raises(self):
        try:
            read_skill_metadata("__nonexistent_skill__")
            assert False, "Should have raised"
        except FileNotFoundError:
            pass
