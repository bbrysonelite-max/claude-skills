import json
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


if __name__ == "__main__":
    unittest.main()
