import json
import unittest
from pathlib import Path

from scripts.common import discover_source_skills, hash_protected_sources


CODEX_SKILLS_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = CODEX_SKILLS_ROOT.parent


class SourceProtectionTests(unittest.TestCase):
    def test_discovers_exact_claude_skill_sources(self):
        sources = discover_source_skills(REPOSITORY_ROOT)

        self.assertEqual(51, len(sources))
        self.assertEqual("agent-reach", sources[0].name)
        self.assertEqual("whitelabel-radar", sources[-1].name)

    def test_source_hash_snapshot_matches_current_sources(self):
        snapshot_path = CODEX_SKILLS_ROOT / "source-hashes.json"
        current_hashes = hash_protected_sources(REPOSITORY_ROOT)
        expected_snapshot = json.dumps(current_hashes, indent=2) + "\n"

        self.assertEqual(expected_snapshot, snapshot_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
