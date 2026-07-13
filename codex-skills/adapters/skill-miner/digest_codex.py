#!/usr/bin/env python3
"""Build skill-miner batches from Codex rollouts and context snapshots."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


_SPACE = re.compile(r"\s+")
_SYSTEM_BLOCK = re.compile(
    r"<(?:system-reminder|environment_context|permissions instructions).*?>.*?"
    r"</(?:system-reminder|environment_context|permissions instructions)>",
    re.DOTALL | re.IGNORECASE,
)
_SECRET_ASSIGNMENT = re.compile(
    r"\b([A-Z][A-Z0-9_]*(?:KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL|AUTH)"
    r"[A-Z0-9_]*)\s*[:=]\s*([^\s,;]+)",
    re.IGNORECASE,
)
_TOKEN_VALUE = re.compile(
    r"\b(?:sk|ghp|github_pat|xox[baprs]|ya29)[-_][A-Za-z0-9_-]{8,}\b"
)
_PRIVATE_KEY = re.compile(
    r"-----BEGIN [^-]+ PRIVATE KEY-----.*?-----END [^-]+ PRIVATE KEY-----",
    re.DOTALL,
)
_NOISE_PREFIXES = (
    "<environment_context>",
    "<permissions instructions>",
    "# AGENTS.md instructions",
)
_OWNED_BATCH_NAME = re.compile(r"batch[1-9][0-9]*\.txt")


@dataclass(frozen=True)
class SessionRecord:
    date: str
    session_id: str
    messages: tuple[tuple[str, str], ...]


def _clean_text(text: str) -> str:
    if text.lstrip().startswith(_NOISE_PREFIXES):
        return ""
    cleaned = _SYSTEM_BLOCK.sub("", text)
    cleaned = _PRIVATE_KEY.sub("<redacted>", cleaned)
    cleaned = _SECRET_ASSIGNMENT.sub(r"\1=<redacted>", cleaned)
    cleaned = _TOKEN_VALUE.sub("<redacted>", cleaned)
    cleaned = _SPACE.sub(" ", cleaned).strip()
    if len(cleaned) > 480:
        return cleaned[:480].rstrip() + "..."
    return cleaned


def _message_text(payload: dict[object, object]) -> tuple[str, str] | None:
    if payload.get("type") != "message":
        return None
    role = payload.get("role")
    if role not in {"user", "assistant"}:
        return None
    content = payload.get("content")
    if not isinstance(content, list):
        return None
    expected_type = "input_text" if role == "user" else "output_text"
    parts: list[str] = []
    for block in content:
        if not isinstance(block, dict) or block.get("type") != expected_type:
            continue
        value = block.get("text")
        if isinstance(value, str):
            parts.append(value)
    text = _clean_text(" ".join(parts))
    return (role, text) if text else None


def _fallback_event_message(
    payload: dict[object, object]
) -> tuple[str, str] | None:
    event_type = payload.get("type")
    role = {"user_message": "user", "agent_message": "assistant"}.get(event_type)
    message = payload.get("message")
    if role is None or not isinstance(message, str):
        return None
    text = _clean_text(message)
    return (role, text) if text else None


def _stable_id(root: Path, path: Path) -> str:
    relative = path.relative_to(root).as_posix()
    return hashlib.sha256(relative.encode("utf-8")).hexdigest()[:8]


def _path_date(root: Path, path: Path) -> str:
    parts = path.relative_to(root).parts
    if (
        len(parts) >= 4
        and len(parts[0]) == 4
        and all(part.isdigit() for part in parts[:3])
    ):
        return "-".join(parts[:3])
    return "?"


def _read_rollout(root: Path, path: Path) -> SessionRecord | None:
    messages: list[tuple[str, str]] = []
    fallback: list[tuple[str, str]] = []
    date = _path_date(root, path)
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as rollout:
            for raw_line in rollout:
                try:
                    event = json.loads(raw_line)
                except (TypeError, ValueError):
                    continue
                if not isinstance(event, dict):
                    continue
                timestamp = event.get("timestamp")
                if date == "?" and isinstance(timestamp, str) and len(timestamp) >= 10:
                    date = timestamp[:10]
                payload = event.get("payload")
                if not isinstance(payload, dict):
                    continue
                if event.get("type") == "response_item":
                    message = _message_text(payload)
                    if message is not None:
                        messages.append(message)
                elif event.get("type") == "event_msg":
                    message = _fallback_event_message(payload)
                    if message is not None:
                        fallback.append(message)
    except OSError:
        return None
    selected = messages or fallback
    if not selected:
        return None
    return SessionRecord(date, _stable_id(root, path), tuple(selected[:80]))


def _read_context_snapshot(root: Path, path: Path) -> SessionRecord | None:
    try:
        text = _clean_text(path.read_text(encoding="utf-8", errors="ignore"))
    except OSError:
        return None
    if not text:
        return None
    return SessionRecord(
        _path_date(root, path),
        _stable_id(root, path),
        (("context", text),),
    )


def collect_sessions(root: Path, limit: int = 0) -> list[SessionRecord]:
    candidates: list[tuple[int, str, Path]] = []
    for path in (*root.rglob("*.jsonl"), *root.rglob("*.md")):
        try:
            mtime = path.stat().st_mtime_ns
        except OSError:
            continue
        candidates.append((mtime, path.relative_to(root).as_posix(), path))
    candidates.sort(key=lambda candidate: (-candidate[0], candidate[1]))
    if limit > 0:
        candidates = candidates[:limit]
    candidates.sort(key=lambda candidate: (candidate[0], candidate[1]))
    sessions: list[SessionRecord] = []
    for _, _, path in candidates:
        record = (
            _read_rollout(root, path)
            if path.suffix == ".jsonl"
            else _read_context_snapshot(root, path)
        )
        if record is not None:
            sessions.append(record)
    return sessions


def _render(sessions: Iterable[SessionRecord]) -> str:
    lines: list[str] = []
    for session in sessions:
        lines.append(
            f"\n===== SESSION {session.session_id}  ({session.date})  - "
            f"{len(session.messages)} messages ====="
        )
        for index, (role, text) in enumerate(session.messages, 1):
            lines.append(f"{index:>2}. [{role}] {text}")
    return "\n".join(lines)


def write_digest(
    sessions: list[SessionRecord], output: Path, batches: int = 0
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    for path in output.parent.glob("batch*.txt"):
        if _OWNED_BATCH_NAME.fullmatch(path.name) and (
            path.is_file() or path.is_symlink()
        ):
            path.unlink()
    header = f"# skill-miner Codex digest - {len(sessions)} sessions"
    if sessions:
        header += f" ({sessions[0].date} .. {sessions[-1].date})"
    output.write_text(header + "\n" + _render(sessions) + "\n", encoding="utf-8")
    if batches > 1 and sessions:
        size = (len(sessions) + batches - 1) // batches
        for index in range(batches):
            chunk = sessions[index * size : (index + 1) * size]
            if not chunk:
                continue
            batch_path = output.parent / f"batch{index + 1}.txt"
            batch_path.write_text(
                f"# batch {index + 1}/{batches}\n" + _render(chunk) + "\n",
                encoding="utf-8",
            )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Digest Codex rollouts for skill-miner."
    )
    parser.add_argument(
        "--dir", type=Path, default=Path.home() / ".codex" / "sessions"
    )
    parser.add_argument(
        "--out", type=Path, default=Path.cwd() / "digest.txt"
    )
    parser.add_argument("--batches", type=int, default=0)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args(argv)
    if args.batches < 0 or args.limit < 0:
        parser.error("--batches and --limit must be non-negative")
    root = args.dir.expanduser().resolve(strict=True)
    if not root.is_dir():
        parser.error(f"session directory is not a directory: {root}")
    sessions = collect_sessions(root, args.limit)
    output = args.out.expanduser().resolve(strict=False)
    write_digest(sessions, output, args.batches)
    print(f"sessions: {len(sessions)}")
    print(f"messages: {sum(len(session.messages) for session in sessions)}")
    print(f"wrote: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
