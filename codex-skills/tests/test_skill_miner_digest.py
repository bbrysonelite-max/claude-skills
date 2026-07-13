import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


CODEX_SKILLS_ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = (
    CODEX_SKILLS_ROOT / "adapters" / "skill-miner" / "digest_codex.py"
)


class SkillMinerCodexDigestTests(unittest.TestCase):
    def _write_rollout(self, path: Path, marker: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        event = {
            "timestamp": "2026-07-12T10:00:00Z",
            "type": "response_item",
            "payload": {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": marker}],
            },
        }
        path.write_text(json.dumps(event) + "\n", encoding="utf-8")

    def _run_helper(
        self, root: Path, output: Path, *extra_arguments: str
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(HELPER_PATH),
                "--dir",
                str(root),
                "--out",
                str(output),
                *extra_arguments,
            ],
            check=True,
            capture_output=True,
            text=True,
        )

    def _assert_limit_backfills_invalid_newest(
        self, newest_content: str
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "sessions"
            newest = root / "a-newest.jsonl"
            older = root / "z-older-valid.jsonl"
            self._write_rollout(older, "OLDER_VALID_MARKER")
            newest.write_text(newest_content, encoding="utf-8")
            os.utime(older, ns=(1_000_000_000, 1_000_000_000))
            os.utime(newest, ns=(2_000_000_000, 2_000_000_000))
            output = Path(temporary_directory) / "digest.txt"

            completed = self._run_helper(root, output, "--limit", "1")

            digest = output.read_text(encoding="utf-8")
            self.assertIn("sessions: 1", completed.stdout)
            self.assertIn("OLDER_VALID_MARKER", digest)

    def test_nested_rollouts_and_context_snapshots_produce_safe_nonempty_batches(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "sessions"
            rollout = root / "2026" / "07" / "12" / "rollout-fixture.jsonl"
            rollout.parent.mkdir(parents=True)
            events = (
                {
                    "timestamp": "2026-07-12T10:00:00Z",
                    "type": "response_item",
                    "payload": {
                        "type": "message",
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": (
                                    "Review the recurring deployment checklist. "
                                    "API_TOKEN=VISIBLE_SECRET"
                                ),
                            }
                        ],
                    },
                },
                {
                    "timestamp": "2026-07-12T10:01:00Z",
                    "type": "response_item",
                    "payload": {
                        "type": "message",
                        "role": "assistant",
                        "content": [
                            {
                                "type": "output_text",
                                "text": "The deployment checklist is recurring.",
                            }
                        ],
                    },
                },
                {
                    "timestamp": "2026-07-12T10:02:00Z",
                    "type": "response_item",
                    "payload": {
                        "type": "function_call",
                        "name": "shell",
                        "arguments": '{"token":"TOOL_PAYLOAD_SECRET"}',
                    },
                },
                {
                    "timestamp": "2026-07-12T10:03:00Z",
                    "type": "response_item",
                    "payload": {
                        "type": "function_call_output",
                        "output": "TOOL_OUTPUT_SECRET",
                    },
                },
                {
                    "timestamp": "2026-07-12T10:04:00Z",
                    "type": "response_item",
                    "payload": {
                        "type": "message",
                        "role": "developer",
                        "content": [
                            {
                                "type": "input_text",
                                "text": "DEVELOPER_CONTEXT_SECRET",
                            }
                        ],
                    },
                },
            )
            rollout.write_text(
                "".join(json.dumps(event) + "\n" for event in events),
                encoding="utf-8",
            )
            snapshot = root / "context-keeper" / "session-snapshot.md"
            snapshot.parent.mkdir()
            snapshot.write_text(
                "# Session Snapshot\n\n"
                "Recurring routine: reconcile release notes after each deploy.\n",
                encoding="utf-8",
            )
            output = Path(temporary_directory) / "digest.txt"

            completed = subprocess.run(
                [
                    sys.executable,
                    str(HELPER_PATH),
                    "--dir",
                    str(root),
                    "--out",
                    str(output),
                    "--batches",
                    "2",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            digest = output.read_text(encoding="utf-8")
            self.assertIn("sessions: 2", completed.stdout)
            self.assertIn("[user] Review the recurring deployment checklist", digest)
            self.assertIn("[assistant] The deployment checklist is recurring", digest)
            self.assertIn("reconcile release notes after each deploy", digest)
            self.assertIn("<redacted>", digest)
            for secret in (
                "VISIBLE_SECRET",
                "TOOL_PAYLOAD_SECRET",
                "TOOL_OUTPUT_SECRET",
                "DEVELOPER_CONTEXT_SECRET",
            ):
                self.assertNotIn(secret, digest)
            batches = sorted(output.parent.glob("batch*.txt"))
            self.assertEqual(2, len(batches))
            self.assertTrue(all(path.stat().st_size > 20 for path in batches))

    def test_limit_selects_newest_rollout_by_mtime(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "sessions"
            newer = root / "a-new.jsonl"
            older = root / "z-old.jsonl"
            self._write_rollout(newer, "NEWEST_ROLLOUT_MARKER")
            self._write_rollout(older, "OLDER_ROLLOUT_MARKER")
            os.utime(older, ns=(1_000_000_000, 1_000_000_000))
            os.utime(newer, ns=(2_000_000_000, 2_000_000_000))
            output = Path(temporary_directory) / "digest.txt"

            completed = self._run_helper(root, output, "--limit", "1")

            digest = output.read_text(encoding="utf-8")
            self.assertIn("sessions: 1", completed.stdout)
            self.assertIn("NEWEST_ROLLOUT_MARKER", digest)
            self.assertNotIn("OLDER_ROLLOUT_MARKER", digest)

    def test_limit_uses_relative_path_to_break_mtime_ties(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "sessions"
            first = root / "a-tied.jsonl"
            second = root / "z-tied.jsonl"
            self._write_rollout(first, "FIRST_PATH_MARKER")
            self._write_rollout(second, "SECOND_PATH_MARKER")
            tied_time = 3_000_000_000
            os.utime(first, ns=(tied_time, tied_time))
            os.utime(second, ns=(tied_time, tied_time))
            output = Path(temporary_directory) / "digest.txt"

            self._run_helper(root, output, "--limit", "1")

            digest = output.read_text(encoding="utf-8")
            self.assertIn("FIRST_PATH_MARKER", digest)
            self.assertNotIn("SECOND_PATH_MARKER", digest)

    def test_limit_applies_to_rollouts_and_context_snapshots_together(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "sessions"
            rollout = root / "rollout.jsonl"
            older_snapshot = root / "context-keeper" / "older.md"
            newer_snapshot = root / "context-keeper" / "newer.md"
            self._write_rollout(rollout, "ROLLOUT_MARKER")
            older_snapshot.parent.mkdir(parents=True)
            older_snapshot.write_text("OLDER_SNAPSHOT_MARKER\n", encoding="utf-8")
            newer_snapshot.write_text("NEWEST_SNAPSHOT_MARKER\n", encoding="utf-8")
            for path, timestamp in (
                (rollout, 1_000_000_000),
                (older_snapshot, 2_000_000_000),
                (newer_snapshot, 3_000_000_000),
            ):
                os.utime(path, ns=(timestamp, timestamp))
            output = Path(temporary_directory) / "digest.txt"

            completed = self._run_helper(root, output, "--limit", "1")

            digest = output.read_text(encoding="utf-8")
            self.assertIn("sessions: 1", completed.stdout)
            self.assertIn("NEWEST_SNAPSHOT_MARKER", digest)
            self.assertNotIn("OLDER_SNAPSHOT_MARKER", digest)
            self.assertNotIn("ROLLOUT_MARKER", digest)

    def test_limit_backfills_after_newest_empty_rollout(self):
        self._assert_limit_backfills_invalid_newest("")

    def test_limit_backfills_after_newest_malformed_rollout(self):
        self._assert_limit_backfills_invalid_newest("{not valid json}\n")

    def test_limit_backfills_after_newest_tool_only_rollout(self):
        tool_only_event = {
            "timestamp": "2026-07-12T10:00:00Z",
            "type": "response_item",
            "payload": {
                "type": "function_call",
                "name": "shell",
                "arguments": "{}",
            },
        }
        self._assert_limit_backfills_invalid_newest(
            json.dumps(tool_only_event) + "\n"
        )

    def test_selected_sessions_render_oldest_first_by_mtime(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "sessions"
            newer = root / "a-new.jsonl"
            older = root / "z-old.jsonl"
            self._write_rollout(newer, "NEWER_RENDER_MARKER")
            self._write_rollout(older, "OLDER_RENDER_MARKER")
            os.utime(older, ns=(1_000_000_000, 1_000_000_000))
            os.utime(newer, ns=(2_000_000_000, 2_000_000_000))
            output = Path(temporary_directory) / "digest.txt"

            self._run_helper(root, output, "--limit", "2")

            digest = output.read_text(encoding="utf-8")
            self.assertLess(
                digest.index("OLDER_RENDER_MARKER"),
                digest.index("NEWER_RENDER_MARKER"),
            )

    def test_rerun_removes_only_stale_owned_batch_files(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "sessions"
            for index in range(1, 4):
                rollout = root / f"session-{index}.jsonl"
                self._write_rollout(rollout, f"SESSION_{index}_MARKER")
                timestamp = index * 1_000_000_000
                os.utime(rollout, ns=(timestamp, timestamp))
            output = Path(temporary_directory) / "digest.txt"
            unrelated = output.parent / "batch-not-owned.txt"
            unrelated.write_text("keep me\n", encoding="utf-8")
            self._run_helper(root, output, "--batches", "3")
            self.assertTrue(all(
                (output.parent / f"batch{index}.txt").is_file()
                for index in range(1, 4)
            ))

            self._run_helper(
                root, output, "--limit", "1", "--batches", "2"
            )

            self.assertTrue((output.parent / "batch1.txt").is_file())
            self.assertFalse((output.parent / "batch2.txt").exists())
            self.assertFalse((output.parent / "batch3.txt").exists())
            self.assertEqual("keep me\n", unrelated.read_text(encoding="utf-8"))
            digest = output.read_text(encoding="utf-8")
            self.assertIn("SESSION_3_MARKER", digest)
            self.assertNotIn("SESSION_1_MARKER", digest)
            self.assertNotIn("SESSION_2_MARKER", digest)


if __name__ == "__main__":
    unittest.main()
