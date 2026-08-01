import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from scripts.sync_active import load_inactive_skills, main


CODEX_SKILLS_ROOT = Path(__file__).resolve().parents[1]
COLLECTION = CODEX_SKILLS_ROOT / "skills"
PROFILE = CODEX_SKILLS_ROOT / "active-profile.json"


class ActiveProfileTests(unittest.TestCase):
    def test_profile_names_the_exact_inactive_capabilities(self):
        self.assertEqual(
            {
                "claude-memory-debug",
                "claude-memory-index",
                "claude-memory-search",
                "claude-memory-status",
                "gitnexus-cli",
                "gitnexus-debugging",
                "gitnexus-exploring",
                "gitnexus-guide",
                "gitnexus-impact-analysis",
                "gitnexus-pr-review",
                "gitnexus-refactoring",
            },
            set(load_inactive_skills(PROFILE)),
        )

    def test_dry_run_installs_only_active_skills(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "skills"
            output = io.StringIO()
            with redirect_stdout(output):
                code = main(
                    [
                        "--source",
                        str(COLLECTION),
                        "--dest",
                        str(destination),
                        "--dry-run",
                        "--json",
                    ]
                )
            result = json.loads(output.getvalue())

        self.assertEqual(0, code, result)
        self.assertEqual(48, len(result["planned_created"]))
        self.assertEqual(11, len(result["excluded"]))
        self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()
