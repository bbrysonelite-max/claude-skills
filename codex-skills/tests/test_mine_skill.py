import re
import unittest
from pathlib import Path


CODEX_SKILLS_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = CODEX_SKILLS_ROOT.parent
MINE_SKILLS = {
    "canonical": REPOSITORY_ROOT / "mine" / "SKILL.md",
    "generated": CODEX_SKILLS_ROOT / "skills" / "mine" / "SKILL.md",
}

FIXED_REMINDER = (
    "**Last30Days freshness reminder:** Before relying on Last30Days to choose "
    "what to mine, check or update the installed skill from "
    "`https://github.com/mvanhorn/last30days-skill`. Do not silently update it; "
    "if the vertical is already selected, show this reminder and continue."
)

EVERY_INVOCATION = re.compile(
    r"(?:\b(?:on|for)\s+)?\bevery\s+"
    r"(?:`?mine`?\s+)?(?:skill\s+)?(?:invocation|run)\b"
    r"|\bevery\s+time\s+(?:the\s+)?`?mine`?(?:\s+skill)?\s+is\s+invoked\b",
    re.IGNORECASE,
)


class MineSkillFreshnessContractTests(unittest.TestCase):
    @staticmethod
    def normalized(text):
        return " ".join(text.split())

    def skill_texts(self):
        for label, path in MINE_SKILLS.items():
            with self.subTest(skill=label):
                self.assertTrue(path.is_file(), path)
            yield label, path.read_text(encoding="utf-8")

    def test_fixed_reminder_is_visible_in_canonical_and_generated_skills(self):
        for label, text in self.skill_texts():
            with self.subTest(skill=label):
                self.assertIn(FIXED_REMINDER, self.normalized(text))

    def test_reminder_is_mandatory_on_every_run_and_precedes_run_instructions(self):
        for label, text in self.skill_texts():
            with self.subTest(skill=label):
                reminder_index = text.find("**Last30Days freshness reminder:**")
                run_index = text.find("## Run it")
                self.assertGreaterEqual(reminder_index, 0, "fixed reminder is missing")
                self.assertGreaterEqual(run_index, 0, "Mine run instructions are missing")
                self.assertLess(reminder_index, run_index)
                self.assertRegex(text[:run_index], EVERY_INVOCATION)

    def test_reminder_is_non_blocking_and_forbids_silent_updates(self):
        for label, text in self.skill_texts():
            with self.subTest(skill=label):
                normalized = self.normalized(text)
                self.assertIn("Do not silently update it", normalized)
                self.assertIn(
                    "if the vertical is already selected, show this reminder and continue",
                    normalized,
                )

    def test_product_boundary_is_explicit_in_both_skills(self):
        last30days_market_selection = re.compile(
            r"Last30Days.{0,180}(?:market[- ]selection|decid(?:e|es|ing)\s+what\s+"
            r"(?:is\s+worth\s+)?mining|choose\s+what\s+to\s+mine)",
            re.IGNORECASE | re.DOTALL,
        )
        mine_raw_ore = re.compile(
            r"(?:Mine|Datamine).{0,140}(?:produces?|finds?)\s+(?:the\s+)?raw\s+ore",
            re.IGNORECASE | re.DOTALL,
        )
        refinery_commercial_leads = re.compile(
            r"refinery.{0,160}(?:produces?|turns?|refines?).{0,100}"
            r"commercial(?:ly)?\s+(?:valuable\s+)?leads",
            re.IGNORECASE | re.DOTALL,
        )

        for label, text in self.skill_texts():
            with self.subTest(skill=label, boundary="Last30Days to market selection"):
                self.assertRegex(text, last30days_market_selection)
            with self.subTest(skill=label, boundary="Mine to raw ore"):
                self.assertRegex(text, mine_raw_ore)
            with self.subTest(skill=label, boundary="refinery to commercial leads"):
                self.assertRegex(text, refinery_commercial_leads)


if __name__ == "__main__":
    unittest.main()
