import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


CODEX_SKILLS_ROOT = Path(__file__).resolve().parents[1]
AUDIT_HELPER = CODEX_SKILLS_ROOT / "adapters" / "skills-librarian" / "audit.py"
BACKUP_HELPER = CODEX_SKILLS_ROOT / "adapters" / "skills-librarian" / "backup.sh"


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
        profile = self.repo / "codex-skills" / "active-profile.json"
        profile.parent.mkdir(parents=True)
        profile.write_text(
            json.dumps({"schema_version": 1, "inactive_skills": []}),
            encoding="utf-8",
        )
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

    def test_active_profile_rejects_an_inactive_live_skill(self):
        profile = self.repo / "codex-skills" / "active-profile.json"
        profile.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "inactive_skills": [
                        {"name": "sample", "reason": "Not active in this harness."}
                    ],
                }
            ),
            encoding="utf-8",
        )
        self.set_cached_current()

        result = self.run_helper(no_fetch=True)

        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("INACTIVE but live: sample", result.stdout)


class LibrarianBackupTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.repo = self.root / "repo"
        self.origin = self.root / "origin.git"
        self.shelf = self.root / "skills"
        self.bin_dir = self.root / "bin"

        skill = self.shelf / "sample"
        skill.mkdir(parents=True)
        skill.joinpath("SKILL.md").write_text(
            "---\nname: sample\ndescription: Use when a sample is needed.\n"
            "---\n\n# Sample\n",
            encoding="utf-8",
        )
        self.git("init", "--bare", str(self.origin), cwd=self.root)
        self.git("init", "-b", "main", str(self.repo), cwd=self.root)
        self.git("config", "user.email", "tests@example.com")
        self.git("config", "user.name", "Test Runner")
        profile = self.repo / "codex-skills" / "active-profile.json"
        profile.parent.mkdir(parents=True)
        profile.write_text(
            json.dumps({"schema_version": 1, "inactive_skills": []}),
            encoding="utf-8",
        )
        provenance = self.repo / ".agents-backup" / "provenance.md"
        provenance.parent.mkdir()
        provenance.write_text("protected provenance\n", encoding="utf-8")
        self.repo.joinpath("reviewed.txt").write_text("before\n", encoding="utf-8")
        self.repo.joinpath(".gitignore").write_text("before\n", encoding="utf-8")
        self.git("add", "-A")
        self.git("commit", "-m", "base")
        self.git("remote", "add", "origin", str(self.origin))
        self.git("push", "-u", "origin", "main")
        self.provenance_before = provenance.read_bytes()

        self.bin_dir.mkdir()
        gh = self.bin_dir / "gh"
        gh.write_text(
            "#!/bin/sh\n"
            'if [ "$1" = "pr" ] && [ "$2" = "create" ]; then\n'
            '  printf "%s\\n" "https://example.test/pull/1"\n'
            "  exit 0\n"
            "fi\n"
            'printf "%s\\n" "unexpected gh invocation" >&2\n'
            "exit 91\n",
            encoding="utf-8",
        )
        gh.chmod(0o755)

        self.repo.joinpath("reviewed.txt").write_text("after\n", encoding="utf-8")
        self.repo.joinpath(".gitignore").write_text(
            "before\nunrelated-user-change\n", encoding="utf-8"
        )

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

    def run_backup(self, *args):
        environment = dict(os.environ)
        environment.update(
            {
                "CODEX_SKILLS_REPO": str(self.repo),
                "SKILLS_DIR": str(self.shelf),
                "PATH": f"{self.bin_dir}{os.pathsep}{environment['PATH']}",
            }
        )
        return subprocess.run(
            ["bash", str(BACKUP_HELPER), *args],
            check=False,
            capture_output=True,
            text=True,
            env=environment,
            timeout=30,
        )

    def assert_provenance_unchanged(self):
        self.assertEqual(
            self.provenance_before,
            self.repo.joinpath(".agents-backup/provenance.md").read_bytes(),
        )

    def test_dry_run_stages_only_explicit_paths_and_preserves_provenance(self):
        result = self.run_backup("--path", "reviewed.txt")

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("DRY RUN", result.stdout)
        self.assertEqual("main", self.git("branch", "--show-current"))
        self.assertEqual("", self.git("diff", "--cached", "--name-only"))
        self.assertEqual(
            [".gitignore", "reviewed.txt"],
            self.git("diff", "--name-only").splitlines(),
        )
        self.assert_provenance_unchanged()

    def test_backup_requires_safe_explicit_path_allowlist(self):
        missing = self.run_backup()
        escaping = self.run_backup("--path", "../outside")
        absolute = self.run_backup("--path", str(self.repo / "reviewed.txt"))

        for result in (missing, escaping, absolute):
            with self.subTest(output=result.stdout + result.stderr):
                self.assertNotEqual(0, result.returncode)
                self.assertIn("path", (result.stdout + result.stderr).casefold())
        self.assertEqual("", self.git("diff", "--cached", "--name-only"))
        self.assert_provenance_unchanged()

    def test_confirm_commits_only_allowlist_and_opens_unmerged_pr(self):
        result = self.run_backup("--confirm", "--path", "reviewed.txt")

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        branch = self.git("branch", "--show-current")
        self.assertRegex(branch, r"^librarian-sync-\d{8}-\d{6}$")
        self.assertEqual(["reviewed.txt"], self.git("show", "--pretty=", "--name-only").splitlines())
        self.assertEqual([".gitignore"], self.git("diff", "--name-only").splitlines())
        self.assertIn("PR OPENED", result.stdout)
        self.assertIn("https://example.test/pull/1", result.stdout)
        self.assertIn(f"origin/{branch}", self.git("branch", "-r").splitlines())
        self.assert_provenance_unchanged()

    def test_codex_helper_has_no_legacy_agent_mirror_or_unbounded_add(self):
        text = BACKUP_HELPER.read_text(encoding="utf-8")

        self.assertIn("CODEX_SKILLS_REPO", text)
        self.assertIn("--path", text)
        self.assertNotIn("AGENTS_SRC", text)
        self.assertNotIn("rsync", text)
        self.assertNotIn("git add -A\n", text)


if __name__ == "__main__":
    unittest.main()
