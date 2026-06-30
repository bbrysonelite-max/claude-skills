import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import dedup  # noqa: E402


class TestNormalize(unittest.TestCase):
    def test_lowercases_and_strips(self):
        self.assertEqual(dedup.normalize("  TikTok:@FezKnowzAI  "), "tiktok:fezknowzai")

    def test_strips_at_without_platform(self):
        self.assertEqual(dedup.normalize("@ToddFalcone"), "toddfalcone")

    def test_empty_becomes_empty(self):
        self.assertEqual(dedup.normalize("   "), "")


class TestLoadSeen(unittest.TestCase):
    def test_ignores_comment_and_blank_lines(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "seen.txt"
            path.write_text("# header comment\n\ninstagram:toddfalcone\n")
            self.assertEqual(dedup.load_seen(path), {"instagram:toddfalcone"})


class TestNewIds(unittest.TestCase):
    def test_filters_already_seen(self):
        seen = {"instagram:toddfalcone"}
        result = dedup.new_ids(["instagram:@ToddFalcone", "tiktok:fezknowzai"], seen)
        self.assertEqual(result, ["tiktok:fezknowzai"])

    def test_dedups_within_batch(self):
        result = dedup.new_ids(["x:harkinsete", "x:@Harkinsete"], set())
        self.assertEqual(result, ["x:harkinsete"])


class TestAddIds(unittest.TestCase):
    def test_appends_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "seen.txt"
            first = dedup.add_ids(path, ["x:harkinsete", "ig:toddfalcone"])
            self.assertEqual(set(first), {"x:harkinsete", "ig:toddfalcone"})
            second = dedup.add_ids(path, ["x:harkinsete", "yt:erfworre"])
            self.assertEqual(second, ["yt:erfworre"])
            lines = [l for l in path.read_text().splitlines() if l.strip()]
            self.assertEqual(len(lines), 3)


class TestCli(unittest.TestCase):
    def test_check_prints_only_new(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "seen.txt"
            path.write_text("instagram:toddfalcone\n")
            out = subprocess.run(
                [sys.executable, str(Path(__file__).parent / "dedup.py"),
                 "--seen", str(path), "--check", "instagram:toddfalcone,tiktok:fezknowzai"],
                capture_output=True, text=True, check=True,
            ).stdout
            self.assertEqual(out.strip(), "tiktok:fezknowzai")


if __name__ == "__main__":
    unittest.main()
