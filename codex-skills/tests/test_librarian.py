import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


CODEX_SKILLS_ROOT = Path(__file__).resolve().parents[1]
AUDIT_HELPER = CODEX_SKILLS_ROOT / "adapters" / "skills-librarian" / "audit.py"


class LibrarianSyncGateTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.repo = self.root / "repo"
        self.shelf = self.root / "skills"
        self.index = self.root / "SKILLS-INDEX.md"
        skill = self.shelf / "sample"
        skill.mkdir(parents=True)
        skill.joinpath("SKILL.md").write_text(
            "---\nname: sample\ndescription: Use when a sample is needed.\n"
            "---\n\n# Sample\n",
            encoding="utf-8",
        )
        self.index.write_text("**sample**\n", encoding="utf-8")
        self.git("init", "-b", "main", str(self.repo), cwd=self.root)
        self.git("config", "user.email", "tests@example.com")
        self.git("config", "user.name", "Test Runner")
        self.repo.joinpath("tracked.txt").write_text("base\n", encoding="utf-8")
        self.git("add", "tracked.txt")
        self.git("commit", "-m", "base")
        self.git("remote", "add", "origin", str(self.root / "missing-origin.git"))

    def git(self, *args, cwd=None):
        command = ["git"]
        if cwd is None:
            command.extend(("-C", str(self.repo)))
        command.extend(args)
        return subprocess.run(
            command,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    def run_helper(self, mode="audit", *, no_fetch=False):
        environment = dict(os.environ)
        environment.update(
            {
                "SKILLS_DIR": str(self.shelf),
                "SKILLS_INDEX": str(self.index),
                "CODEX_SKILLS_REPO": str(self.repo),
            }
        )
        if no_fetch:
            environment["SKILLS_NO_FETCH"] = "1"
        else:
            environment.pop("SKILLS_NO_FETCH", None)
        return subprocess.run(
            [sys.executable, str(AUDIT_HELPER), mode],
            check=False,
            capture_output=True,
            text=True,
            env=environment,
            timeout=30,
        )

    def set_cached_current(self):
        head = self.git("rev-parse", "HEAD")
        self.git("update-ref", "refs/remotes/origin/main", head)

    def set_cached_behind(self):
        base = self.git("rev-parse", "HEAD")
        self.repo.joinpath("tracked.txt").write_text("newer\n", encoding="utf-8")
        self.git("commit", "-am", "newer")
        newer = self.git("rev-parse", "HEAD")
        self.git("update-ref", "refs/remotes/origin/main", newer)
        self.git("reset", "--hard", base)

    def test_fetch_failure_still_fails_when_cached_ref_is_behind(self):
        self.set_cached_behind()

        result = self.run_helper()

        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("SHELF IS STALE", result.stdout)
        self.assertIn("cached", result.stdout.casefold())
        self.assertIn("fetch", result.stdout.casefold())

    def test_cached_current_is_explicitly_degraded_after_fetch_failure_or_skip(self):
        self.set_cached_current()

        for label, no_fetch in (("fetch failure", False), ("explicit skip", True)):
            with self.subTest(label=label):
                result = self.run_helper(no_fetch=no_fetch)
                self.assertEqual(0, result.returncode, result.stdout + result.stderr)
                self.assertIn("cached comparison", result.stdout.casefold())
                self.assertIn("upstream freshness is unverified", result.stdout.casefold())

    def test_missing_cached_ref_is_unverified_and_nonzero_for_audit_and_diff(self):
        for mode in ("audit", "diff-index"):
            with self.subTest(mode=mode):
                result = self.run_helper(mode, no_fetch=True)
                self.assertNotEqual(0, result.returncode, result.stdout + result.stderr)
                self.assertIn("unverified", result.stdout.casefold())
                self.assertIn("no origin/main", result.stdout.casefold())


if __name__ == "__main__":
    unittest.main()
