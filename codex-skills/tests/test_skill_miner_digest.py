import json
import os
import stat
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

    def _run_helper_failure(
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
            check=False,
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
            output = Path(temporary_directory) / "scratch" / "digest.txt"

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
            output = Path(temporary_directory) / "scratch" / "digest.txt"

            completed = subprocess.run(
                [
                    sys.executable,
                    str(HELPER_PATH),
                    "--dir",
                    str(root),
                    "--out",
                    str(output),
                    "--context-dir",
                    str(snapshot.parent),
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
            output = Path(temporary_directory) / "scratch" / "digest.txt"

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
            output = Path(temporary_directory) / "scratch" / "digest.txt"

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
            output = Path(temporary_directory) / "scratch" / "digest.txt"

            completed = self._run_helper(
                root,
                output,
                "--context-dir",
                str(older_snapshot.parent),
                "--limit",
                "1",
            )

            digest = output.read_text(encoding="utf-8")
            self.assertIn("sessions: 1", completed.stdout)
            self.assertIn("NEWEST_SNAPSHOT_MARKER", digest)
            self.assertNotIn("OLDER_SNAPSHOT_MARKER", digest)
            self.assertNotIn("ROLLOUT_MARKER", digest)

    def test_explicit_project_context_root_is_included_in_digest_and_batches(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary = Path(temporary_directory)
            rollout_root = temporary / "global-rollouts"
            project_context = temporary / "project" / ".codex" / "sessions"
            self._write_rollout(
                rollout_root / "rollout.jsonl", "GLOBAL_ROLLOUT_MARKER"
            )
            (rollout_root / "not-a-project-snapshot.md").write_text(
                "GLOBAL_MARKDOWN_MUST_BE_IGNORED\n", encoding="utf-8"
            )
            project_context.mkdir(parents=True)
            snapshot = project_context / "2026-07-13_session-1.md"
            snapshot.write_text(
                "PROJECT_CONTEXT_MARKER API_TOKEN=CONTEXT_SECRET\n",
                encoding="utf-8",
            )
            output = temporary / "scratch" / "digest.txt"

            completed = self._run_helper(
                rollout_root,
                output,
                "--context-dir",
                str(project_context),
                "--batches",
                "2",
            )

            digest = output.read_text(encoding="utf-8")
            batch_text = "\n".join(
                path.read_text(encoding="utf-8")
                for path in sorted(output.parent.glob("batch*.txt"))
            )
            self.assertIn("sessions: 2", completed.stdout)
            self.assertIn("GLOBAL_ROLLOUT_MARKER", digest)
            self.assertIn("PROJECT_CONTEXT_MARKER", digest)
            self.assertIn("PROJECT_CONTEXT_MARKER", batch_text)
            self.assertNotIn("GLOBAL_MARKDOWN_MUST_BE_IGNORED", digest)
            self.assertIn("<redacted>", digest)
            self.assertNotIn("CONTEXT_SECRET", digest)

    def test_repeatable_context_roots_are_deduplicated_before_limit_and_order(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary = Path(temporary_directory)
            rollout_root = temporary / "global-rollouts"
            context_root = temporary / "project" / ".codex" / "sessions"
            rollout = rollout_root / "rollout.jsonl"
            snapshot = context_root / "snapshot.md"
            self._write_rollout(rollout, "OLDER_ROLLOUT_MARKER")
            context_root.mkdir(parents=True)
            snapshot.write_text("NEWER_CONTEXT_MARKER\n", encoding="utf-8")
            os.utime(rollout, ns=(1_000_000_000, 1_000_000_000))
            os.utime(snapshot, ns=(2_000_000_000, 2_000_000_000))
            output = temporary / "scratch" / "digest.txt"

            completed = self._run_helper(
                rollout_root,
                output,
                "--context-dir",
                str(context_root),
                "--context-dir",
                str(context_root),
                "--limit",
                "1",
            )

            digest = output.read_text(encoding="utf-8")
            self.assertIn("sessions: 1", completed.stdout)
            self.assertIn("NEWER_CONTEXT_MARKER", digest)
            self.assertNotIn("OLDER_ROLLOUT_MARKER", digest)

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
            output = Path(temporary_directory) / "scratch" / "digest.txt"

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
            output = Path(temporary_directory) / "scratch" / "digest.txt"
            self._run_helper(root, output, "--batches", "3")
            marker = output.parent / ".skill-miner-digest-owned"
            self.assertEqual(
                "skill-miner-digest scratch v1\n",
                marker.read_text(encoding="utf-8"),
            )
            self.assertEqual(0o700, stat.S_IMODE(output.parent.stat().st_mode))
            for private_file in (output, marker, output.parent / "batch1.txt"):
                self.assertEqual(
                    0o600, stat.S_IMODE(private_file.stat().st_mode)
                )
            unrelated = output.parent / "batch-not-owned.txt"
            unrelated.write_text("keep me\n", encoding="utf-8")
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

    def test_redacts_exact_common_credentials_and_private_key_blocks(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary = Path(temporary_directory)
            root = temporary / "rollouts"
            assignments = {
                "PASSWORD": "ExactPasswordValue",
                "TOKEN": "ExactTokenValue",
                "SECRET": "ExactSecretValue",
                "KEY": "ExactKeyValue",
                "DB_PASSWORD": "DatabasePasswordValue",
                "API_TOKEN": "ApiTokenValue",
                "CLIENT_SECRET": "ClientSecretValue",
                "OPENAI_API_KEY": "ApiKeyValue",
            }
            assignment_text = " ".join(
                f"{name}={value}" for name, value in assignments.items()
            )
            self._write_rollout(
                root / "assignments.jsonl",
                f"ASSIGNMENT_MARKER {assignment_text}",
            )
            key_types = ("PRIVATE", "RSA PRIVATE", "EC PRIVATE", "OPENSSH PRIVATE")
            key_bodies = []
            for index, key_type in enumerate(key_types, 1):
                body = f"FAKE_PRIVATE_KEY_BODY_{index}_MUST_NOT_APPEAR"
                key_bodies.append(body)
                self._write_rollout(
                    root / f"key-{index}.jsonl",
                    f"KEY_MARKER_{index}\n-----BEGIN {key_type} KEY-----\n"
                    f"{body}\n-----END {key_type} KEY-----",
                )
            output = temporary / "scratch" / "digest.txt"

            self._run_helper(root, output)

            digest = output.read_text(encoding="utf-8")
            self.assertIn("ASSIGNMENT_MARKER", digest)
            self.assertIn("<redacted>", digest)
            for value in (*assignments.values(), *key_bodies):
                self.assertNotIn(value, digest)
            for key_type in key_types:
                self.assertNotIn(f"BEGIN {key_type} KEY", digest)
                self.assertNotIn(f"END {key_type} KEY", digest)

    def test_redacts_quoted_and_structured_credentials_without_value_tails(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary = Path(temporary_directory)
            root = temporary / "rollouts"
            credential_text = (
                'JSON_MARKER {"password": "json correct horse", '
                '"api_token": "json api token"}\n'
                "SINGLE_JSON_MARKER {'password': 'single json secret', "
                "'api_token': 'single api token'}\n"
                'ASSIGNMENT_MARKER PASSWORD="Correct Horse Battery Staple" '
                "TOKEN='multi word token secret'\n"
                "YAML_MARKER\npassword: yaml-unquoted-secret\n"
                'api_token: "yaml quoted multiword secret"\n'
                "client_secret: 'yaml single quoted secret'\n"
                "auth: yaml unquoted multiword secret\n"
                r'ESCAPED_MARKER PASSWORD="secret with an escaped \"quote\" tail"'
            )
            self._write_rollout(root / "credentials.jsonl", credential_text)
            output = temporary / "scratch" / "digest.txt"

            self._run_helper(root, output)

            digest = output.read_text(encoding="utf-8")
            for marker in (
                "JSON_MARKER",
                "SINGLE_JSON_MARKER",
                "ASSIGNMENT_MARKER",
                "YAML_MARKER",
                "ESCAPED_MARKER",
            ):
                self.assertIn(marker, digest)
            for secret_fragment in (
                "json correct horse",
                "json api token",
                "single json secret",
                "single api token",
                "Correct Horse Battery Staple",
                "multi word token secret",
                "yaml-unquoted-secret",
                "yaml quoted multiword secret",
                "yaml single quoted secret",
                "yaml unquoted multiword secret",
                "escaped",
                "quote",
                "tail",
            ):
                self.assertNotIn(secret_fragment, digest)
            for redacted_shape in (
                '"password": "<redacted>"',
                '"api_token": "<redacted>"',
                "'password': '<redacted>'",
                "'api_token': '<redacted>'",
                'PASSWORD="<redacted>"',
                "TOKEN='<redacted>'",
                "password: <redacted>",
                'api_token: "<redacted>"',
                "client_secret: '<redacted>'",
                "auth: <redacted>",
            ):
                self.assertIn(redacted_shape, digest)
            self.assertEqual(2, digest.count('PASSWORD="<redacted>"'))

    def test_rejects_output_equal_to_or_inside_input_root(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "rollouts"
            rollout = root / "rollout.jsonl"
            self._write_rollout(rollout, "INPUT_MUST_SURVIVE")
            original = rollout.read_bytes()

            equal = self._run_helper_failure(root, rollout)
            inside = self._run_helper_failure(
                root, root / "scratch" / "digest.txt"
            )

            self.assertNotEqual(0, equal.returncode)
            self.assertNotEqual(0, inside.returncode)
            self.assertEqual(original, rollout.read_bytes())
            self.assertFalse((root / "scratch").exists())

    def test_rejects_output_symlink_and_symlinked_parent(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary = Path(temporary_directory)
            root = temporary / "rollouts"
            rollout = root / "rollout.jsonl"
            self._write_rollout(rollout, "INPUT_MUST_SURVIVE")
            scratch = temporary / "scratch"
            scratch.mkdir()
            output_link = scratch / "digest.txt"
            output_link.symlink_to(rollout)
            linked_parent = temporary / "linked-scratch"
            linked_parent.symlink_to(root, target_is_directory=True)
            outside = temporary / "outside"
            existing_child = outside / "existing-child"
            existing_child.mkdir(parents=True)
            linked_ancestor = temporary / "linked-ancestor"
            linked_ancestor.symlink_to(outside, target_is_directory=True)

            direct = self._run_helper_failure(root, output_link)
            parent = self._run_helper_failure(
                root, linked_parent / "digest.txt"
            )
            ancestor = self._run_helper_failure(
                root, linked_ancestor / existing_child.name / "digest.txt"
            )

            self.assertNotEqual(0, direct.returncode)
            self.assertNotEqual(0, parent.returncode)
            self.assertNotEqual(0, ancestor.returncode)
            self.assertIn("INPUT_MUST_SURVIVE", rollout.read_text(encoding="utf-8"))

    def test_rejects_nonempty_unowned_scratch_directory(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary = Path(temporary_directory)
            root = temporary / "rollouts"
            self._write_rollout(root / "rollout.jsonl", "ROLLOUT_MARKER")
            scratch = temporary / "scratch"
            scratch.mkdir()
            unrelated = scratch / "unrelated.txt"
            unrelated.write_text("preserve me\n", encoding="utf-8")

            completed = self._run_helper_failure(
                root, scratch / "digest.txt"
            )

            self.assertNotEqual(0, completed.returncode)
            self.assertEqual("preserve me\n", unrelated.read_text(encoding="utf-8"))
            self.assertFalse((scratch / "digest.txt").exists())

    def test_project_root_is_resolved_before_changing_to_external_scratch(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary = Path(temporary_directory)
            repo = temporary / "project"
            nested = repo / "nested"
            context = repo / ".codex" / "sessions"
            rollouts = temporary / "rollouts"
            scratch = temporary / "external-scratch"
            nested.mkdir(parents=True)
            context.mkdir(parents=True)
            snapshot = context / "snapshot.md"
            snapshot.write_text("ORDERED_PROJECT_CONTEXT\n", encoding="utf-8")
            self._write_rollout(rollouts / "rollout.jsonl", "ROLLOUT_MARKER")
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            command = (
                'PROJECT_ROOT="$(git rev-parse --show-toplevel)"\n'
                'mkdir -m 700 "$1"\n'
                'cd "$1"\n'
                'python3 "$2" --dir "$3" --context-dir '
                '"$PROJECT_ROOT/.codex/sessions" --out "$1/digest.txt"\n'
            )

            subprocess.run(
                [
                    "bash",
                    "-c",
                    command,
                    "test-script",
                    str(scratch),
                    str(HELPER_PATH),
                    str(rollouts),
                ],
                cwd=nested,
                check=True,
                capture_output=True,
                text=True,
            )

            digest = (scratch / "digest.txt").read_text(encoding="utf-8")
            self.assertIn("ORDERED_PROJECT_CONTEXT", digest)


if __name__ == "__main__":
    unittest.main()
