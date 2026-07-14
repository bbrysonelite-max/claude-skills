import os
import re
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path


CODEX_SKILLS_ROOT = Path(__file__).resolve().parents[1]
ADAPTER_SCRIPT = (
    CODEX_SKILLS_ROOT / "adapters" / "context-keeper" / "new-session.sh"
)


class ContextKeeperAdapterTests(unittest.TestCase):
    def test_script_has_valid_bash_syntax_and_executable_mode(self):
        completed = subprocess.run(
            ["bash", "-n", str(ADAPTER_SCRIPT)],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertTrue(ADAPTER_SCRIPT.stat().st_mode & stat.S_IXUSR)

    def test_forty_concurrent_writers_create_unique_complete_snapshots(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            session_dir = Path(temporary_directory) / "sessions"
            environment = dict(os.environ, CONTEXT_KEEPER_DIR=str(session_dir))
            processes = [
                subprocess.Popen(
                    ["bash", str(ADAPTER_SCRIPT), f"concurrent arc {index}"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=environment,
                )
                for index in range(40)
            ]
            results = [process.communicate(timeout=30) for process in processes]

            created_paths = []
            for process, (stdout, stderr) in zip(processes, results):
                self.assertEqual(0, process.returncode, stderr)
                match = re.fullmatch(r"CREATED: (.+)\n", stdout)
                self.assertIsNotNone(match, stdout)
                created_paths.append(Path(match.group(1)))
            self.assertEqual(40, len(set(created_paths)))
            snapshots = sorted(session_dir.glob("*_session-*.md"))
            self.assertEqual(40, len(snapshots))
            numbers = sorted(
                int(re.search(r"session-(\d+)\.md$", path.name).group(1))
                for path in snapshots
            )
            self.assertEqual(list(range(1, 41)), numbers)
            for index, path in enumerate(created_paths):
                text = path.read_text(encoding="utf-8")
                self.assertIn(f"concurrent arc {index}", text)
                self.assertIn("## 1. Decisions", text)
                self.assertIn("## 4. Verified vs unverified", text)
                self.assertEqual(0o644, stat.S_IMODE(path.stat().st_mode))
            self.assertEqual([], list(session_dir.glob(".new-session-*")))


if __name__ == "__main__":
    unittest.main()
