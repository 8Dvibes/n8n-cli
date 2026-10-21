import re
import unittest
from importlib import resources


def _skill_dirs():
    root = resources.files("n8n_cli.skills_data")
    return sorted(
        entry for entry in root.iterdir() if (entry / "SKILL.md").is_file()
    )


def _frontmatter_name(text):
    match = re.match(r"---\n(.*?)\n---\n", text, re.DOTALL)
    assert match, "SKILL.md has no frontmatter block"
    name = re.search(r"^name:\s*(\S+)\s*$", match.group(1), re.MULTILINE)
    assert name, "frontmatter has no name field"
    return name.group(1)


class SkillNamesTest(unittest.TestCase):
    def test_frontmatter_name_matches_directory(self):
        for skill in _skill_dirs():
            text = (skill / "SKILL.md").read_text(encoding="utf-8")
            self.assertEqual(
                _frontmatter_name(text),
                skill.name,
                "frontmatter name must equal the installed directory name",
            )

    def test_heading_slash_command_matches_directory(self):
        for skill in _skill_dirs():
            if not skill.name.startswith("n8n-cli-"):
                continue
            text = (skill / "SKILL.md").read_text(encoding="utf-8")
            heading = re.search(r"^# /(\S+)", text, re.MULTILINE)
            if heading:
                self.assertEqual(heading.group(1), skill.name)

    def test_slash_references_resolve_to_installed_skills(self):
        installed = {skill.name for skill in _skill_dirs()}
        pattern = re.compile(r"(?<![\w./~-])/(n8n-cli-[a-z0-9-]+)")
        for skill in _skill_dirs():
            text = (skill / "SKILL.md").read_text(encoding="utf-8")
            for ref in pattern.findall(text):
                self.assertIn(
                    ref,
                    installed,
                    "%s references /%s, which is not an installed skill"
                    % (skill.name, ref),
                )

    def test_no_legacy_short_slash_names(self):
        legacy = re.compile(
            r"(?<![\w./~-])/n8n-(status|debug|create|import|export|monitor"
            r"|migrate|backup|diff|webhook-test|creds)(?![\w-])"
        )
        for skill in _skill_dirs():
            text = (skill / "SKILL.md").read_text(encoding="utf-8")
            self.assertIsNone(
                legacy.search(text),
                "%s still documents a legacy /n8n-<verb> command" % skill.name,
            )


if __name__ == "__main__":
    unittest.main()
