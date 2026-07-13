#!/usr/bin/env python3
"""Build skill-miner batches from Codex rollouts and context snapshots."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


_SPACE = re.compile(r"\s+")
_SYSTEM_BLOCK = re.compile(
    r"<(?:system-reminder|environment_context|permissions instructions).*?>.*?"
    r"</(?:system-reminder|environment_context|permissions instructions)>",
    re.DOTALL | re.IGNORECASE,
)
_CREDENTIAL_TERM = r"(?:PASSWORD|TOKEN|SECRET|KEY|CREDENTIAL|AUTH)"
_CREDENTIAL_NAME = (
    rf"(?:{_CREDENTIAL_TERM}|[A-Z][A-Z0-9_.-]*{_CREDENTIAL_TERM})"
)
_CREDENTIAL_KEY = (
    rf'(?:"{_CREDENTIAL_NAME}"|\'{_CREDENTIAL_NAME}\'|{_CREDENTIAL_NAME})'
)
_BARE_CREDENTIAL_VALUE = r"[^\]}\r\n,;]*?"
_CREDENTIAL_VALUE_DELIMITER = r"[\]},;\r\n]"
_SECRET_ASSIGNMENT = re.compile(
    rf"""
    (?P<prefix>
        (?<![A-Z0-9_.-])
        {_CREDENTIAL_KEY}
        \s*[:=]\s*
    )
    (?P<value>
        "(?:\\.|[^"\\])*"
        | '(?:\\.|[^'\\])*'
        | {_BARE_CREDENTIAL_VALUE}
          (?=
              \s*(?:{_CREDENTIAL_VALUE_DELIMITER}|\Z)
              | \s+(?={_CREDENTIAL_KEY}\s*[:=])
          )
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)
_YAML_CREDENTIAL_BLOCK_HEADER = re.compile(
    rf"^(?P<indent> *)(?P<key>{_CREDENTIAL_KEY})[ \t]*:[ \t]*"
    r"[|>](?:[1-9][+-]?|[+-][1-9]?)?[ \t]*(?:#[^\r\n]*)?"
    r"(?P<newline>\r\n|\r|\n|\Z)$",
    re.IGNORECASE,
)
_TOKEN_VALUE = re.compile(
    r"\b(?:sk|ghp|github_pat|xox[baprs]|ya29)[-_][A-Za-z0-9_-]{8,}\b"
)
_PRIVATE_KEY = re.compile(
    r"-----BEGIN (?P<label>(?:(?:RSA|EC|OPENSSH) )?PRIVATE KEY)-----.*?"
    r"-----END (?P=label)-----",
    re.DOTALL,
)
_NOISE_PREFIXES = (
    "<environment_context>",
    "<permissions instructions>",
    "# AGENTS.md instructions",
)
_OWNED_BATCH_NAME = re.compile(r"batch[1-9][0-9]*\.txt")
_OWNER_MARKER_NAME = ".skill-miner-digest-owned"
_OWNER_MARKER_CONTENT = "skill-miner-digest scratch v1\n"


@dataclass(frozen=True)
class SessionRecord:
    date: str
    session_id: str
    messages: tuple[tuple[str, str], ...]


def _redact_secret_assignment(match: re.Match[str]) -> str:
    value = match.group("value")
    if len(value) >= 2 and value[0] in {"'", '"'} and value[-1] == value[0]:
        redacted = f"{value[0]}<redacted>{value[0]}"
    else:
        redacted = "<redacted>"
    return match.group("prefix") + redacted


def _redact_yaml_credential_blocks(text: str) -> str:
    lines = text.splitlines(keepends=True)
    redacted: list[str] = []
    index = 0
    while index < len(lines):
        header = _YAML_CREDENTIAL_BLOCK_HEADER.fullmatch(lines[index])
        if header is None:
            redacted.append(lines[index])
            index += 1
            continue

        redacted.append(
            f"{header.group('indent')}{header.group('key')}: <redacted>"
            f"{header.group('newline')}"
        )
        header_indent = len(header.group("indent"))
        index += 1
        while index < len(lines):
            body_line = lines[index]
            if not body_line.strip(" \t\r\n"):
                index += 1
                continue
            body_indent = len(body_line) - len(body_line.lstrip(" "))
            if body_indent <= header_indent:
                break
            index += 1
    return "".join(redacted)


def _clean_text(text: str) -> str:
    if text.lstrip().startswith(_NOISE_PREFIXES):
        return ""
    cleaned = _SYSTEM_BLOCK.sub("", text)
    cleaned = _redact_yaml_credential_blocks(cleaned)
    cleaned = _PRIVATE_KEY.sub("<redacted>", cleaned)
    cleaned = _SECRET_ASSIGNMENT.sub(_redact_secret_assignment, cleaned)
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
    identity = f"{root.resolve().as_posix()}::{relative}"
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()[:8]


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


def _collect_candidates(
    root: Path,
    pattern: str,
    kind: str,
    candidates: dict[Path, tuple[int, str, Path, Path, str]],
) -> None:
    resolved_root = root.resolve(strict=True)
    for path in root.rglob(pattern):
        try:
            resolved_path = path.resolve(strict=True)
            if (
                not resolved_path.is_file()
                or not resolved_path.is_relative_to(resolved_root)
            ):
                continue
            mtime = resolved_path.stat().st_mtime_ns
        except (OSError, RuntimeError):
            continue
        identity = f"{kind}:{resolved_path.as_posix()}"
        candidates.setdefault(
            resolved_path,
            (mtime, identity, resolved_root, resolved_path, kind),
        )


def collect_sessions(
    root: Path,
    limit: int = 0,
    context_roots: Iterable[Path] = (),
) -> list[SessionRecord]:
    candidates_by_path: dict[Path, tuple[int, str, Path, Path, str]] = {}
    _collect_candidates(root, "*.jsonl", "rollout", candidates_by_path)
    for context_root in context_roots:
        _collect_candidates(
            context_root, "*.md", "context", candidates_by_path
        )
    candidates = sorted(
        candidates_by_path.values(),
        key=lambda candidate: (-candidate[0], candidate[1]),
    )
    selected: list[tuple[int, str, SessionRecord]] = []
    for mtime, identity, candidate_root, path, kind in candidates:
        record = (
            _read_rollout(candidate_root, path)
            if kind == "rollout"
            else _read_context_snapshot(candidate_root, path)
        )
        if record is not None:
            selected.append((mtime, identity, record))
            if limit > 0 and len(selected) == limit:
                break
    selected.sort(key=lambda session: (session[0], session[1]))
    return [record for _, _, record in selected]


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


def _normalized_absolute(path: Path) -> Path:
    expanded = path.expanduser()
    if not expanded.is_absolute():
        expanded = Path.cwd() / expanded
    lexical = Path(os.path.abspath(expanded))
    parts = lexical.parts
    candidate = Path(lexical.anchor)
    remaining = parts[1:]

    # macOS exposes trusted temporary roots through top-level aliases such as
    # /var -> /private/var. Normalize only that protected prefix, then reject
    # every lower symlink component instead of following it.
    if len(remaining) > 1:
        top_level = candidate / remaining[0]
        if top_level.exists() or top_level.is_symlink():
            candidate = top_level.resolve(strict=True)
            remaining = remaining[1:]
    for part in remaining:
        candidate = candidate / part
        if candidate.is_symlink():
            raise ValueError(
                f"output path must not contain symlinks: {candidate}"
            )
    return candidate


def _reject_symlink_components(path: Path) -> None:
    for candidate in (*reversed(path.parents), path):
        if candidate.is_symlink():
            raise ValueError(
                f"output path must not contain symlinks: {candidate}"
            )


def _paths_overlap(left: Path, right: Path) -> bool:
    return (
        left == right
        or left.is_relative_to(right)
        or right.is_relative_to(left)
    )


def _prepare_scratch(output: Path, input_roots: Iterable[Path]) -> Path:
    _reject_symlink_components(output)
    scratch = output.parent
    for input_root in input_roots:
        if _paths_overlap(scratch, input_root):
            raise ValueError(
                f"output directory overlaps input directory: {scratch}"
            )

    if scratch.exists() and not scratch.is_dir():
        raise ValueError(f"output directory is not a directory: {scratch}")
    scratch.mkdir(mode=0o700, parents=True, exist_ok=True)
    _reject_symlink_components(output)
    scratch.chmod(0o700)

    marker = scratch / _OWNER_MARKER_NAME
    if marker.is_symlink():
        raise ValueError(f"scratch ownership marker must not be a symlink: {marker}")
    if marker.exists():
        if not marker.is_file():
            raise ValueError(f"invalid scratch ownership marker: {marker}")
        try:
            marker_content = marker.read_text(encoding="utf-8")
        except OSError as error:
            raise ValueError(
                f"cannot read scratch ownership marker: {marker}"
            ) from error
        if marker_content != _OWNER_MARKER_CONTENT:
            raise ValueError(f"invalid scratch ownership marker: {marker}")
    else:
        if any(scratch.iterdir()):
            raise ValueError(
                f"refusing nonempty unowned output directory: {scratch}"
            )
        try:
            with marker.open("x", encoding="utf-8") as marker_file:
                marker_file.write(_OWNER_MARKER_CONTENT)
            marker.chmod(0o600)
        except FileExistsError:
            raise ValueError(
                f"scratch ownership marker appeared concurrently: {marker}"
            ) from None
    return output


def _write_private_text(path: Path, text: str) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags, 0o600)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as output_file:
            descriptor = -1
            output_file.write(text)
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def _write_atomic_private_text(path: Path, text: str) -> None:
    descriptor, temp_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temp_path: Path | None = Path(temp_name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as output_file:
            descriptor = -1
            output_file.write(text)
            output_file.flush()
            os.fsync(output_file.fileno())
        os.replace(temp_path, path)
        temp_path = None
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if temp_path is not None:
            try:
                temp_path.unlink()
            except FileNotFoundError:
                pass


def write_digest(
    sessions: list[SessionRecord], output: Path, batches: int = 0
) -> None:
    for path in output.parent.glob("batch*.txt"):
        if _OWNED_BATCH_NAME.fullmatch(path.name) and (
            path.is_file() or path.is_symlink()
        ):
            path.unlink()
    header = f"# skill-miner Codex digest - {len(sessions)} sessions"
    if sessions:
        header += f" ({sessions[0].date} .. {sessions[-1].date})"
    _write_atomic_private_text(
        output, header + "\n" + _render(sessions) + "\n"
    )
    if batches > 1 and sessions:
        size = (len(sessions) + batches - 1) // batches
        for index in range(batches):
            chunk = sessions[index * size : (index + 1) * size]
            if not chunk:
                continue
            batch_path = output.parent / f"batch{index + 1}.txt"
            _write_private_text(
                batch_path,
                f"# batch {index + 1}/{batches}\n" + _render(chunk) + "\n",
            )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Digest Codex rollouts for skill-miner."
    )
    parser.add_argument(
        "--dir", type=Path, default=Path.home() / ".codex" / "sessions"
    )
    parser.add_argument(
        "--context-dir",
        action="append",
        default=[],
        type=Path,
        help=(
            "project-local .codex/sessions directory containing Markdown "
            "context snapshots; repeat for multiple projects"
        ),
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
    context_roots: list[Path] = []
    seen_context_roots: set[Path] = set()
    for context_candidate in args.context_dir:
        context_root = context_candidate.expanduser().resolve(strict=True)
        if not context_root.is_dir():
            parser.error(
                f"context directory is not a directory: {context_root}"
            )
        if context_root not in seen_context_roots:
            seen_context_roots.add(context_root)
            context_roots.append(context_root)
    try:
        output = _normalized_absolute(args.out)
        _prepare_scratch(output, (root, *context_roots))
    except (OSError, ValueError) as error:
        parser.error(str(error))
    sessions = collect_sessions(root, args.limit, context_roots)
    write_digest(sessions, output, args.batches)
    print(f"sessions: {len(sessions)}")
    print(f"messages: {sum(len(session.messages) for session in sessions)}")
    print(f"wrote: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
