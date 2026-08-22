from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from agent_practice.skill import default_skill_path, load_skill


class SkillTests(unittest.TestCase):
    def test_loads_standard_skill(self) -> None:
        skill = load_skill(default_skill_path())

        self.assertEqual(skill.name, "workshop-planner")
        self.assertIn("Agent", skill.description)
        self.assertIn("design_workshop_agenda", skill.instructions)

    def test_rejects_name_that_does_not_match_directory(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "different-name" / "SKILL.md"
            path.parent.mkdir()
            path.write_text(
                "---\n"
                "name: workshop-planner\n"
                "description: Valid description\n"
                "---\n"
                "Do the work.\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "必须与目录名"):
                load_skill(path)


if __name__ == "__main__":
    unittest.main()
