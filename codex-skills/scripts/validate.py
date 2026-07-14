#!/usr/bin/env python3

import argparse
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from dataclasses import dataclass, replace
from datetime import date
from hashlib import sha256
from pathlib import Path
from urllib.parse import unquote

try:
    from scripts.adapt import validate_generated_markdown
    from scripts.build import (
        GENERATED_ADAPTER_RESOURCES,
        GENERATED_MARKER,
        PROMOTED_PROVENANCE,
        build_collection,
    )
    from scripts.common import (
        SAFE_SKILL_NAME,
        Manifest,
        SkillEntry,
        hash_protected_sources,
        load_manifest,
        parse_skill_document,
    )
except ModuleNotFoundError:  # Support direct execution as scripts/validate.py.
    from adapt import validate_generated_markdown  # type: ignore[no-redef]
    from build import (  # type: ignore[no-redef]
        GENERATED_ADAPTER_RESOURCES,
        GENERATED_MARKER,
        PROMOTED_PROVENANCE,
        build_collection,
    )
    from common import (  # type: ignore[no-redef]
        SAFE_SKILL_NAME,
        Manifest,
        SkillEntry,
        hash_protected_sources,
        load_manifest,
        parse_skill_document,
    )


EXPECTED_SKILL_COUNT = 58
EXPECTED_SOURCE_COUNT = 51
EXPECTED_PROMOTED_COUNT = 7
EXPECTED_CLASS_COUNTS = {
    "adapted": 9,
    "dependency-required": 43,
    "native": 6,
}
EXPECTED_RUNTIME_COUNT = 52
OFFICIAL_VALIDATOR = Path(
    "/Users/brentbryson/.codex/skills/.system/skill-creator/scripts/quick_validate.py"
)
OFFICIAL_COMMAND_PREFIX = ("uv", "run", "--with", "pyyaml", "python")
INTERFACE_FIELDS = {"display_name", "short_description", "default_prompt"}
EXCLUDED_RESOURCE_PARTS = {
    ".cache",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "build",
    "cache",
    "dist",
    "fixtures",
    "node_modules",
    "vendor",
}
LOCAL_RESOURCE = re.compile(
    r"(?<![\w./-])"
    r"((?:\./)?(?:scripts|references|assets|templates|verticals|bin)/"
    r"[A-Za-z0-9_.@%+()/\\-]+)"
)
REFERENCE_DEFINITION = re.compile(
    r"(?m)^[ \t]{0,3}\[([^\]\n]+)\]:[ \t]*"
)
REPORT_FINGERPRINT = re.compile(
    r"(?m)^- \*\*Structural fingerprint:\*\* `([0-9a-f]{64})`$"
)
STRUCTURAL_REPORT_SCHEMA = 1
TARGET_PROJECT_RESOURCE_LINES = {
    ("here-now", "references/REFERENCE.md"): frozenset(
        {
            '    { "path": "assets/app.js", "size": 999, "contentType": "text/javascript; charset=utf-8", "hash": "e5f6a7b8..." }',
            '    "ogImagePath": "assets/cover.png"',
            "- `files` (required): array of `{ path, size, contentType, hash }`. At least one file. Paths should be relative to the site root (e.g. `index.html`, `assets/style.css`) — don't include a parent directory name like `my-project/index.html`.",
            '    "skipped": ["assets/app.js"],',
        }
    ),
    ("whitelabel-radar", "SKILL.md"): frozenset(
        {
            "> the right entities, segment, act. Clone it for other verticals/intents (recruits, partners, buyers).",
        }
    ),
}
PLACEHOLDER = re.compile(
    r"\{\{[A-Z_][A-Z0-9_]*\}\}|<<[A-Z_][A-Z0-9_]*>>|"
    r"__PLACEHOLDER__|\b(?:TODO|TBD):\s*replace\b|<PLACEHOLDER>",
    re.IGNORECASE,
)
ACTIVE_CLAUDE_PATH = re.compile(r"(?:(?:~|\$HOME)/)?\.claude/")
PROMOTED_COUPLING = re.compile(
    r"(?:\bGSD\b|\.planning/|\borchestrator\b|\bslash command\b)",
    re.IGNORECASE,
)
MANDATORY_DEPENDENCY_HEADING = "Mandatory dependencies:"
SECRET_CLAUSE = "Never expose or print secret, credential, or token values."
OVERRIDE_SECRET_CLAUSE = "Never print, log, or expose secret values."
PREFLIGHT_CLAUSE = "Preflight each dependency using MCP/app capability discovery"
BLOCKED_CLAUSE = "If any mandatory dependency is unavailable"

ALLOWED_CLAUDE_PATH_LINES = frozenset(
    {
        "Read historical `.claude/sessions/` as evidence.",
        (
            "Treat historical `.claude/sessions/` files as read-only evidence; never "
            "write new snapshots there."
        ),
        (
            "Treat historical `~/.claude/projects/-Users-brentbryson-Desktop-vault-"
            "personal/memory/` files as read-only evidence; never update or delete "
            "them. Record current corrections in the vault's current documentation "
            "and indexes."
        ),
        (
            "Use historical `~/.claude/projects/-Users-brentbryson/*.jsonl` only as "
            "read-only evidence with the original `scripts/digest.py`; never use that "
            "helper for current Codex rollouts."
        ),
    }
)


@dataclass(frozen=True)
class SyntaxValidation:
    language: str
    interpreter: str
    paths: tuple[str, ...]
    errors: tuple[str, ...]

    @property
    def count(self) -> int:
        return len(self.paths)

    @property
    def ok(self) -> bool:
        return not self.errors


@dataclass(frozen=True)
class OfficialValidation:
    name: str
    passed: bool
    output: str
    execution_mode: str = "online"
    initial_diagnostic: str = ""


@dataclass(frozen=True)
class RegressionValidation:
    interpreter: str
    tests_run: int
    passed: bool
    diagnostic: str


@dataclass(frozen=True)
class InjectedDefectValidation:
    category: str
    name: str
    passed: bool
    diagnostic: str


@dataclass(frozen=True)
class DependencyProbe:
    dependency: str
    status: str


@dataclass(frozen=True)
class DependencyStatus:
    name: str
    dependencies: tuple[str, ...]
    status: str
    probes: tuple[DependencyProbe, ...] = ()


@dataclass(frozen=True)
class SkillValidation:
    path: Path
    name: str
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    markdown_count: int
    syntax_results: tuple[SyntaxValidation, ...]

    @property
    def ok(self) -> bool:
        return not self.errors


@dataclass(frozen=True)
class CollectionReport:
    repo_root: Path
    generated_on: str
    skill_results: tuple[SkillValidation, ...]
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    class_counts: tuple[tuple[str, int], ...]
    source_hash_count: int
    source_hashes_match: bool
    markdown_count: int
    resource_count: int
    runtime_count: int
    native_runtime_absent_count: int
    dependency_preflight_count: int
    dependency_secret_count: int
    syntax_results: tuple[SyntaxValidation, ...]
    official_results: tuple[OfficialValidation, ...]
    dependency_statuses: tuple[DependencyStatus, ...]
    installed_count: int | None
    source_only: bool
    approved_existing_count: int | None = None
    structural_fingerprint: str = ""
    regression_results: tuple[RegressionValidation, ...] = ()
    injected_defect_results: tuple[InjectedDefectValidation, ...] = ()
    excluded: tuple[str, ...] = ()

    @classmethod
    def empty(
        cls, repo_root: Path, *, errors: tuple[str, ...] = ()
    ) -> "CollectionReport":
        return cls(
            repo_root=Path(repo_root),
            generated_on=date.today().isoformat(),
            skill_results=(),
            errors=errors,
            warnings=(),
            class_counts=(),
            source_hash_count=0,
            source_hashes_match=not errors,
            markdown_count=0,
            resource_count=0,
            runtime_count=0,
            native_runtime_absent_count=0,
            dependency_preflight_count=0,
            dependency_secret_count=0,
            syntax_results=(),
            official_results=(),
            dependency_statuses=(),
            installed_count=None,
            source_only=False,
            structural_fingerprint=_structural_fingerprint(Path(repo_root)),
        )

    @property
    def skill_count(self) -> int:
        return len(self.skill_results)

    @property
    def official_failures(self) -> int:
        return sum(not result.passed for result in self.official_results)

    @property
    def official_passes(self) -> int:
        return sum(result.passed for result in self.official_results)

    @property
    def excluded_count(self) -> int:
        return len(self.excluded)

    @property
    def ok(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict:
        return {
            "repo_root": str(self.repo_root),
            "generated_on": self.generated_on,
            "ok": self.ok,
            "source_only": self.source_only,
            "skill_count": self.skill_count,
            "class_counts": dict(self.class_counts),
            "source_hash_count": self.source_hash_count,
            "source_hashes_match": self.source_hashes_match,
            "markdown_count": self.markdown_count,
            "resource_count": self.resource_count,
            "runtime_count": self.runtime_count,
            "native_runtime_absent_count": self.native_runtime_absent_count,
            "dependency_preflight_count": self.dependency_preflight_count,
            "dependency_secret_count": self.dependency_secret_count,
            "syntax": [
                {
                    "language": result.language,
                    "interpreter": result.interpreter,
                    "count": result.count,
                    "paths": list(result.paths),
                    "errors": list(result.errors),
                }
                for result in self.syntax_results
            ],
            "official": {
                "passes": self.official_passes,
                "failures": self.official_failures,
                "results": [
                    {
                        "name": result.name,
                        "passed": result.passed,
                        "output": result.output,
                        "execution_mode": result.execution_mode,
                        "initial_diagnostic": result.initial_diagnostic,
                    }
                    for result in self.official_results
                ],
            },
            "regression_suites": [
                {
                    "interpreter": result.interpreter,
                    "tests_run": result.tests_run,
                    "passed": result.passed,
                    "diagnostic": result.diagnostic,
                }
                for result in self.regression_results
            ],
            "injected_defects": [
                {
                    "category": result.category,
                    "name": result.name,
                    "passed": result.passed,
                    "diagnostic": result.diagnostic,
                }
                for result in self.injected_defect_results
            ],
            "dependencies": [
                {
                    "name": result.name,
                    "dependencies": list(result.dependencies),
                    "status": result.status,
                    "probes": [
                        {
                            "dependency": probe.dependency,
                            "status": probe.status,
                        }
                        for probe in result.probes
                    ],
                }
                for result in self.dependency_statuses
            ],
            "installed_count": self.installed_count,
            "managed_installed_count": self.installed_count,
            "approved_existing_count": self.approved_existing_count,
            "excluded": list(self.excluded),
            "excluded_count": self.excluded_count,
            "structural_fingerprint": self.structural_fingerprint,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }


def _read_text(path: Path) -> tuple[str | None, str | None]:
    try:
        with path.open("r", encoding="utf-8", newline="") as input_file:
            return input_file.read(), None
    except (OSError, UnicodeError) as error:
        return None, f"{path}: cannot read UTF-8 text: {error}"


def _frontmatter_keys(text: str) -> tuple[str, ...]:
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        return ()
    keys: list[str] = []
    for line in lines[1:]:
        if line == "---":
            break
        if not line.strip() or line.lstrip().startswith("#") or line[:1].isspace():
            continue
        if ":" in line:
            keys.append(line.split(":", 1)[0])
    return tuple(keys)


def _parse_scalar(raw: str) -> str:
    value = raw.strip()
    if value.startswith(('"', "'")):
        if value.startswith('"'):
            parsed = json.loads(value)
            if not isinstance(parsed, str):
                raise ValueError("metadata scalar must be a string")
            return parsed
        if not value.endswith("'"):
            raise ValueError("unterminated metadata scalar")
        return value[1:-1].replace("''", "'")
    return value


def _parse_openai_metadata(text: str) -> dict[str, str]:
    lines = text.splitlines()
    if not lines or lines[0] != "interface:":
        raise ValueError("agents/openai.yaml top level must contain only interface")
    values: dict[str, str] = {}
    for line in lines[1:]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line.startswith("  ") or line.startswith("   ") or ":" not in line:
            raise ValueError("agents/openai.yaml contains malformed interface data")
        key, raw = line[2:].split(":", 1)
        if key in values:
            raise ValueError(f"agents/openai.yaml duplicates interface field {key}")
        values[key] = _parse_scalar(raw)
    return values


def _line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _is_templated_target(target: str) -> bool:
    return bool(
        re.search(r"\{[^}]+\}|<[^>]+>|\$\{[^}]+\}|\*", target)
    ) or target.lower() in {"url", "path", "file", "filename"}


def _unescape_markdown(value: str) -> str:
    return re.sub(r"\\([\\`*{}\[\]()#+.!_<>-])", r"\1", value)


def _link_target(raw: str) -> str:
    target = _unescape_markdown(raw.strip())
    return unquote(target).split("#", 1)[0].split("?", 1)[0]


def _closing_bracket(text: str, start: int) -> int | None:
    depth = 1
    index = start + 1
    while index < len(text):
        character = text[index]
        if character == "\\":
            index += 2
            continue
        if character == "[":
            depth += 1
        elif character == "]":
            depth -= 1
            if depth == 0:
                return index
        index += 1
    return None


def _markdown_destination(
    text: str, start: int, *, inline: bool
) -> tuple[str, int] | None:
    index = start
    while index < len(text) and text[index] in " \t":
        index += 1
    if index >= len(text) or text[index] == "\n":
        return None
    if text[index] == "<":
        index += 1
        characters: list[str] = []
        while index < len(text):
            character = text[index]
            if character == "\\" and index + 1 < len(text):
                characters.extend((character, text[index + 1]))
                index += 2
                continue
            if character == ">":
                return "".join(characters), index + 1
            if character == "\n":
                return None
            characters.append(character)
            index += 1
        return None

    depth = 0
    characters = []
    while index < len(text):
        character = text[index]
        if character == "\\" and index + 1 < len(text):
            characters.extend((character, text[index + 1]))
            index += 2
            continue
        if character == "(":
            depth += 1
            characters.append(character)
            index += 1
            continue
        if character == ")":
            if inline and depth == 0:
                return "".join(characters), index + 1
            if depth > 0:
                depth -= 1
            characters.append(character)
            index += 1
            continue
        if character in " \t\n" and depth == 0:
            return "".join(characters), index
        characters.append(character)
        index += 1
    if inline:
        return None
    return "".join(characters), index


def _reference_label(value: str) -> str:
    return " ".join(_unescape_markdown(value).split()).casefold()


def _markdown_destinations(text: str) -> tuple[tuple[str, int], ...]:
    definitions: dict[str, str] = {}
    for match in REFERENCE_DEFINITION.finditer(text):
        parsed = _markdown_destination(text, match.end(), inline=False)
        if parsed is not None and parsed[0]:
            definitions.setdefault(_reference_label(match.group(1)), parsed[0])

    destinations: list[tuple[str, int]] = []
    index = 0
    while index < len(text):
        if text[index] != "[" or (index > 0 and text[index - 1] == "\\"):
            index += 1
            continue
        close = _closing_bracket(text, index)
        if close is None:
            break
        next_index = close + 1
        line_start = text.rfind("\n", 0, index) + 1
        if (
            next_index < len(text)
            and text[next_index] == ":"
            and not text[line_start:index].strip()
        ):
            index = next_index + 1
            continue
        if next_index < len(text) and text[next_index] == "(":
            parsed = _markdown_destination(text, next_index + 1, inline=True)
            if parsed is not None:
                destinations.append((parsed[0], index))
                index = parsed[1]
                continue
        elif next_index < len(text) and text[next_index] == "[":
            reference_close = _closing_bracket(text, next_index)
            if reference_close is not None:
                label = text[next_index + 1 : reference_close]
                if not label:
                    label = text[index + 1 : close]
                target = definitions.get(_reference_label(label))
                if target is not None:
                    destinations.append((target, index))
                index = reference_close + 1
                continue
        else:
            target = definitions.get(
                _reference_label(text[index + 1 : close])
            )
            if target is not None:
                destinations.append((target, index))
        index = close + 1
    return tuple(destinations)


def _check_local_target(
    skill_root: Path,
    markdown_path: Path,
    target: str,
    line: int,
    errors: list[str],
) -> None:
    if (
        not target
        or target.startswith(("http://", "https://", "mailto:", "data:", "#"))
        or _is_templated_target(target)
    ):
        return
    candidate = Path(target)
    if candidate.is_absolute():
        return
    resolved = (markdown_path.parent / candidate).resolve(strict=False)
    collection_root = skill_root.parent.resolve(strict=False)
    if not resolved.is_relative_to(collection_root):
        errors.append(
            f"{markdown_path.name}:{line}: local link escapes generated collection: {target}"
        )
        return
    if not resolved.exists():
        errors.append(f"{markdown_path.name}:{line}: broken local link: {target}")


def _validate_markdown(
    skill_root: Path, markdown_path: Path, text: str, errors: list[str]
) -> None:
    relative = markdown_path.relative_to(skill_root).as_posix()
    if "\r\n" in text:
        errors.append(f"{relative}: CRLF newlines are not normalized")
    if "\r" in text.replace("\r\n", ""):
        errors.append(f"{relative}: bare carriage return found")
    placeholder = PLACEHOLDER.search(text)
    if placeholder:
        errors.append(
            f"{relative}:{_line_number(text, placeholder.start())}: unresolved placeholder "
            f"marker {placeholder.group(0)!r}"
        )
    try:
        validate_generated_markdown(skill_root.name, relative, text)
    except ValueError as error:
        errors.append(str(error))
    for line_number, line in enumerate(text.splitlines(), start=1):
        if ACTIVE_CLAUDE_PATH.search(line) and line.strip() not in ALLOWED_CLAUDE_PATH_LINES:
            errors.append(
                f"{relative}:{line_number}: active Claude path is not allowlisted"
            )
    for raw_target, offset in _markdown_destinations(text):
        target = _link_target(raw_target)
        _check_local_target(
            skill_root,
            markdown_path,
            target,
            _line_number(text, offset),
            errors,
        )
    for match in LOCAL_RESOURCE.finditer(text):
        target = _unescape_markdown(match.group(1)).rstrip(".,;:")
        while target.endswith(")") and target.count(")") > target.count("("):
            target = target[:-1]
        if _is_templated_target(target):
            continue
        line_number = _line_number(text, match.start())
        source_line = text.splitlines()[line_number - 1]
        if source_line in TARGET_PROJECT_RESOURCE_LINES.get(
            (skill_root.name, relative), frozenset()
        ):
            continue
        candidates = (markdown_path.parent / target, skill_root / target)
        if not any(candidate.exists() for candidate in candidates):
            errors.append(
                f"{relative}:{line_number}: referenced local "
                f"resource does not exist: {target}"
            )


def _validate_symlinks(skill_root: Path, errors: list[str]) -> None:
    for current, directory_names, file_names in os.walk(
        skill_root, topdown=True, followlinks=False
    ):
        current_path = Path(current)
        for name in sorted(directory_names + file_names):
            path = current_path / name
            if not path.is_symlink():
                continue
            relative = path.relative_to(skill_root).as_posix()
            try:
                target = path.resolve(strict=True)
            except (FileNotFoundError, RuntimeError) as error:
                errors.append(f"{relative}: broken symlink: {error}")
                continue
            if not target.is_relative_to(skill_root.resolve()):
                errors.append(f"{relative}: symlink escapes skill directory")


def _resource_paths(skill_root: Path, suffixes: set[str]) -> list[Path]:
    paths: list[Path] = []
    for path in skill_root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in suffixes:
            continue
        relative = path.relative_to(skill_root)
        if any(part in EXCLUDED_RESOURCE_PARTS for part in relative.parts):
            continue
        paths.append(path)
    return sorted(paths, key=lambda path: path.relative_to(skill_root).as_posix())


def _command_version(executable: str) -> str:
    try:
        result = subprocess.run(
            [executable, "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        return executable
    version = (result.stdout or result.stderr).strip().splitlines()
    return f"{version[0] if version else executable} ({executable})"


def _run_syntax_command(
    command: list[str], path: Path, *, env: dict[str, str] | None = None
) -> str | None:
    try:
        result = subprocess.run(
            [*command, str(path)],
            check=False,
            capture_output=True,
            text=True,
            timeout=90,
            env=env,
        )
    except (OSError, subprocess.SubprocessError) as error:
        return f"{path}: syntax checker failed to run: {error}"
    if result.returncode == 0:
        return None
    detail = (result.stderr or result.stdout).strip().replace("\n", " | ")
    return f"{path}: syntax check failed: {detail}"


def _syntax_checks(skill_root: Path) -> tuple[SyntaxValidation, ...]:
    results: list[SyntaxValidation] = []
    python_paths = _resource_paths(skill_root, {".py"})

    for executable in _python_executables():
        errors: list[str] = []
        with tempfile.TemporaryDirectory(prefix="codex-skill-pycache-") as cache:
            environment = dict(os.environ)
            environment["PYTHONPYCACHEPREFIX"] = cache
            for path in python_paths:
                error = _run_syntax_command(
                    [executable, "-m", "py_compile"], path, env=environment
                )
                if error:
                    errors.append(error)
        results.append(
            SyntaxValidation(
                "python",
                _command_version(executable),
                tuple(path.relative_to(skill_root).as_posix() for path in python_paths),
                tuple(errors),
            )
        )

    shell_paths = _resource_paths(skill_root, {".sh"})
    bash = shutil.which("bash")
    if bash:
        errors = tuple(
            error
            for path in shell_paths
            if (error := _run_syntax_command([bash, "-n"], path))
        )
        results.append(
            SyntaxValidation(
                "shell",
                _command_version(bash),
                tuple(path.relative_to(skill_root).as_posix() for path in shell_paths),
                errors,
            )
        )

    javascript_paths = _resource_paths(skill_root, {".js", ".cjs", ".mjs"})
    node = shutil.which("node")
    if node:
        errors = tuple(
            error
            for path in javascript_paths
            if (error := _run_syntax_command([node, "--check"], path))
        )
        results.append(
            SyntaxValidation(
                "javascript",
                _command_version(node),
                tuple(path.relative_to(skill_root).as_posix() for path in javascript_paths),
                errors,
            )
        )
    return tuple(results)


def _python_executables() -> tuple[str, ...]:
    executables: list[str] = []
    default_python = shutil.which("python3") or sys.executable
    executables.append(default_python)
    python311 = shutil.which("python3.11")
    if python311 and Path(python311).resolve() != Path(default_python).resolve():
        executables.append(python311)
    return tuple(executables)


def validate_skill(path: Path, *, run_syntax: bool = True) -> SkillValidation:
    """Validate one generated skill and accumulate every independent failure."""
    skill_root = Path(path)
    errors: list[str] = []
    warnings: list[str] = []
    name = skill_root.name
    if skill_root.is_symlink() or not skill_root.is_dir():
        errors.append(f"{skill_root}: skill path must be a real directory")
        return SkillValidation(skill_root, name, tuple(errors), (), 0, ())
    if SAFE_SKILL_NAME.fullmatch(name) is None or len(name) > 64:
        errors.append(f"{name}: folder name violates Codex naming limits")

    skill_path = skill_root / "SKILL.md"
    skill_text, skill_read_error = _read_text(skill_path)
    if skill_read_error:
        errors.append(skill_read_error)
    elif skill_text is not None:
        keys = _frontmatter_keys(skill_text)
        if len(keys) != 2 or set(keys) != {"name", "description"}:
            errors.append(
                f"{name}/SKILL.md: frontmatter must contain only name and description"
            )
        try:
            document = parse_skill_document(skill_text)
        except ValueError as error:
            errors.append(f"{name}/SKILL.md: invalid frontmatter: {error}")
        else:
            if document.name != name:
                errors.append(
                    f"{name}/SKILL.md: frontmatter name {document.name!r} does not "
                    "match folder"
                )
            if len(document.name) > 64:
                errors.append(f"{name}/SKILL.md: name exceeds 64 characters")
            if len(document.description) > 1024:
                errors.append(f"{name}/SKILL.md: description exceeds 1024 characters")
            if "<" in document.description or ">" in document.description:
                errors.append(
                    f"{name}/SKILL.md: description cannot contain angle brackets"
                )

    metadata_path = skill_root / "agents" / "openai.yaml"
    metadata_text, metadata_read_error = _read_text(metadata_path)
    if metadata_read_error:
        errors.append(metadata_read_error)
    elif metadata_text is not None:
        try:
            interface = _parse_openai_metadata(metadata_text)
        except (ValueError, json.JSONDecodeError) as error:
            errors.append(f"{name}/agents/openai.yaml: {error}")
        else:
            if set(interface) != INTERFACE_FIELDS:
                errors.append(
                    f"{name}/agents/openai.yaml: interface fields must be exactly "
                    f"{sorted(INTERFACE_FIELDS)}"
                )
            short = interface.get("short_description", "")
            if not short or len(short) > 100:
                errors.append(
                    f"{name}/agents/openai.yaml: short_description must be 1-100 characters"
                )
            default_prompt = interface.get("default_prompt", "")
            if f"${name}" not in default_prompt:
                errors.append(
                    f"{name}/agents/openai.yaml: default_prompt must contain ${name}"
                )
            if not interface.get("display_name", "").strip():
                errors.append(
                    f"{name}/agents/openai.yaml: display_name must be non-empty"
                )

    _validate_symlinks(skill_root, errors)
    markdown_paths = sorted(
        (
            path
            for path in skill_root.rglob("*.md")
            if path.is_file() and "vendor" not in path.relative_to(skill_root).parts
        ),
        key=lambda path: path.relative_to(skill_root).as_posix(),
    )
    for markdown_path in markdown_paths:
        text, read_error = _read_text(markdown_path)
        if read_error:
            errors.append(read_error)
            continue
        _validate_markdown(skill_root, markdown_path, text or "", errors)

    syntax_results = _syntax_checks(skill_root) if run_syntax else ()
    for result in syntax_results:
        errors.extend(result.errors)
    return SkillValidation(
        skill_root,
        name,
        tuple(errors),
        tuple(warnings),
        len(markdown_paths),
        syntax_results,
    )


def _validate_source_hashes(repo_root: Path) -> tuple[int, bool, list[str]]:
    errors: list[str] = []
    snapshot_path = repo_root / "codex-skills" / "source-hashes.json"
    try:
        expected = json.loads(snapshot_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        return 0, False, [f"source hash snapshot cannot be read: {error}"]
    if not isinstance(expected, dict) or not all(
        isinstance(path, str) and isinstance(digest, str)
        for path, digest in expected.items()
    ):
        return 0, False, ["source hash snapshot must map paths to digests"]
    try:
        current = hash_protected_sources(repo_root)
    except (OSError, RuntimeError) as error:
        return len(expected), False, [f"protected sources cannot be hashed: {error}"]
    missing = sorted(set(expected) - set(current))
    extra = sorted(set(current) - set(expected))
    changed = sorted(
        path for path in set(expected) & set(current) if expected[path] != current[path]
    )
    if missing:
        errors.append("source hash drift, missing protected paths: " + ", ".join(missing))
    if extra:
        errors.append("source hash drift, extra protected paths: " + ", ".join(extra))
    if changed:
        errors.append("source hash drift, changed protected paths: " + ", ".join(changed))
    return len(current), not errors, errors


def _validate_manifest_contract(
    manifest: Manifest, errors: list[str]
) -> tuple[tuple[str, int], ...]:
    counts = {
        conversion: sum(entry.conversion == conversion for entry in manifest.entries)
        for conversion in sorted(EXPECTED_CLASS_COUNTS)
    }
    if len(manifest.sources) != EXPECTED_SOURCE_COUNT:
        errors.append(
            f"manifest must contain exactly {EXPECTED_SOURCE_COUNT} source skills, "
            f"found {len(manifest.sources)}"
        )
    if len(manifest.promoted) != EXPECTED_PROMOTED_COUNT:
        errors.append(
            f"manifest must contain exactly {EXPECTED_PROMOTED_COUNT} promoted skills, "
            f"found {len(manifest.promoted)}"
        )
    if len(manifest.entries) != EXPECTED_SKILL_COUNT:
        errors.append(
            f"manifest must contain exactly {EXPECTED_SKILL_COUNT} outputs, "
            f"found {len(manifest.entries)}"
        )
    for conversion, expected in sorted(EXPECTED_CLASS_COUNTS.items()):
        if counts[conversion] != expected:
            errors.append(
                f"manifest class {conversion} must contain {expected}, "
                f"found {counts[conversion]}"
            )
    for entry in manifest.sources:
        if entry.source != entry.output:
            errors.append(
                f"manifest source/output renaming is not allowed: {entry.source} -> {entry.output}"
            )
    for entry in manifest.promoted:
        expected = PROMOTED_PROVENANCE.get(entry.output)
        if expected is None or entry.promoted_from != expected:
            errors.append(
                f"promoted provenance mismatch for {entry.output}: "
                f"expected {expected!r}, got {entry.promoted_from!r}"
            )
        if entry.conversion != "adapted" or entry.dependencies:
            errors.append(
                f"promoted entry {entry.output} must be adapted without dependencies"
            )
    return tuple(sorted(counts.items()))


def _directory_snapshot(root: Path) -> dict[str, tuple[str, int, str]]:
    snapshot: dict[str, tuple[str, int, str]] = {}
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix()
        mode = stat.S_IMODE(path.lstat().st_mode)
        if path.is_symlink():
            snapshot[relative] = ("symlink", mode, os.readlink(path))
        elif path.is_dir():
            snapshot[relative] = ("directory", mode, "")
        elif path.is_file():
            snapshot[relative] = ("file", mode, sha256(path.read_bytes()).hexdigest())
    return snapshot


def _structural_fingerprint(repo_root: Path) -> str:
    root = Path(repo_root).expanduser().resolve(strict=False)
    codex_root = root / "codex-skills"
    contract_paths = (
        codex_root / "manifest.yaml",
        codex_root / "source-hashes.json",
        codex_root / "scripts" / "adapt.py",
        codex_root / "scripts" / "build.py",
        codex_root / "scripts" / "common.py",
        codex_root / "scripts" / "validate.py",
    )
    contract: dict[str, tuple[str, int, str]] = {}
    for path in contract_paths:
        relative = path.relative_to(root).as_posix()
        try:
            mode = stat.S_IMODE(path.lstat().st_mode)
            if path.is_file() and not path.is_symlink():
                contract[relative] = (
                    "file",
                    mode,
                    sha256(path.read_bytes()).hexdigest(),
                )
            elif path.is_symlink():
                contract[relative] = ("symlink", mode, os.readlink(path))
            else:
                contract[relative] = ("missing", mode, "")
        except OSError:
            contract[relative] = ("missing", 0, "")
    payload = {
        "schema": STRUCTURAL_REPORT_SCHEMA,
        "contract": contract,
        "generated": _directory_snapshot(codex_root / "skills")
        if (codex_root / "skills").is_dir()
        else {},
    }
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _validate_expected_parity(
    repo_root: Path, manifest: Manifest, output_root: Path, errors: list[str]
) -> None:
    try:
        with tempfile.TemporaryDirectory(prefix="codex-skills-validation-") as temporary:
            expected_root = Path(temporary) / "skills"
            build_collection(repo_root, manifest, expected_root)
            expected = _directory_snapshot(expected_root)
            actual = _directory_snapshot(output_root)
    except (OSError, RuntimeError, ValueError, KeyError) as error:
        errors.append(f"could not build normalized parity snapshot: {error}")
        return
    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    changed = sorted(
        path for path in set(expected) & set(actual) if expected[path] != actual[path]
    )
    if missing:
        errors.append("normalized output parity missing paths: " + ", ".join(missing))
    if extra:
        errors.append("normalized output parity extra paths: " + ", ".join(extra))
    if changed:
        errors.append("normalized output parity changed paths: " + ", ".join(changed))


def _mandatory_dependencies(body: str) -> tuple[str, ...]:
    lines = body.splitlines()
    override_prefix = "- **Dependencies:**"
    override_index = next(
        (index for index, line in enumerate(lines) if line.startswith(override_prefix)),
        None,
    )
    if override_index is not None:
        dependencies: list[str] = []
        for line in lines[override_index + 1 :]:
            if not line.startswith("- `") or not line.endswith("`"):
                break
            dependencies.append(line[3:-1])
        return tuple(dependencies)
    try:
        index = lines.index(MANDATORY_DEPENDENCY_HEADING)
    except ValueError:
        return ()
    dependencies: list[str] = []
    for line in lines[index + 1 :]:
        if not line.startswith("- `") or not line.endswith("`"):
            break
        dependencies.append(line[3:-1])
    return tuple(dependencies)


def _validate_runtime_contracts(
    manifest: Manifest,
    output_root: Path,
    errors: list[str],
) -> tuple[int, int, int, int]:
    runtime_count = 0
    native_absent = 0
    dependency_preflight = 0
    dependency_secret = 0
    for entry in manifest.entries:
        path = output_root / entry.output / "SKILL.md"
        text, read_error = _read_text(path)
        if read_error or text is None:
            continue
        try:
            body = parse_skill_document(text).body
        except ValueError:
            continue
        count = body.count("## Codex Runtime")
        runtime_count += count
        if entry.conversion == "native":
            if count == 0:
                native_absent += 1
            else:
                errors.append(f"{entry.output}: native skill must not add Codex Runtime")
        elif count != 1:
            errors.append(
                f"{entry.output}: {entry.conversion} skill must contain exactly one "
                "Codex Runtime section"
            )
        if entry.conversion == "dependency-required":
            observed_dependencies = _mandatory_dependencies(body)
            if observed_dependencies != entry.dependencies:
                errors.append(
                    f"{entry.output}: runtime dependency list does not match manifest; "
                    f"expected {entry.dependencies!r}, found {observed_dependencies!r}"
                )
            has_preflight = (
                PREFLIGHT_CLAUSE in body and BLOCKED_CLAUSE in body
            ) or body.count("## Inputs and Preflight") == 1
            if has_preflight:
                dependency_preflight += 1
            else:
                errors.append(
                    f"{entry.output}: dependency runtime is missing preflight/blocked clauses"
                )
            if SECRET_CLAUSE in body or OVERRIDE_SECRET_CLAUSE in body:
                dependency_secret += 1
            else:
                errors.append(
                    f"{entry.output}: dependency runtime is missing the no-secret clause"
                )
        if entry in manifest.promoted:
            for markdown_path in sorted((output_root / entry.output).rglob("*.md")):
                markdown_text, markdown_error = _read_text(markdown_path)
                if markdown_error or markdown_text is None:
                    continue
                if PROMOTED_COUPLING.search(markdown_text):
                    relative = markdown_path.relative_to(output_root / entry.output)
                    errors.append(
                        f"{entry.output}/{relative}: promoted runtime coupling to "
                        "GSD/planning found"
                    )
    if len(manifest.entries) == EXPECTED_SKILL_COUNT:
        if runtime_count != EXPECTED_RUNTIME_COUNT:
            errors.append(
                f"generated collection must contain {EXPECTED_RUNTIME_COUNT} runtime "
                f"sections, found {runtime_count}"
            )
        if native_absent != EXPECTED_CLASS_COUNTS["native"]:
            errors.append(
                f"all {EXPECTED_CLASS_COUNTS['native']} native skills must omit runtime "
                f"sections, observed {native_absent}"
            )
        if dependency_preflight != EXPECTED_CLASS_COUNTS["dependency-required"]:
            errors.append(
                "all dependency-required skills must have preflights; observed "
                f"{dependency_preflight}"
            )
        if dependency_secret != EXPECTED_CLASS_COUNTS["dependency-required"]:
            errors.append(
                "all dependency-required skills must have no-secret clauses; observed "
                f"{dependency_secret}"
            )
    return runtime_count, native_absent, dependency_preflight, dependency_secret


def _sanitize_official_diagnostic(output: str) -> str:
    normalized = output.lower()
    if "pyyaml" in normalized and (
        "dns error" in normalized or "failed to lookup address" in normalized
    ):
        return "uv PyYAML dependency resolution failed because DNS lookup failed"
    return "official validator dependency resolution failed"


def _normalize_official_output(output: str) -> str:
    return re.sub(
        r"(Request failed after \d+ retries) in \d+(?:\.\d+)?s",
        r"\1",
        output.strip(),
    )


def run_official_validation(
    skill_paths: tuple[Path, ...] | list[Path],
) -> tuple[OfficialValidation, ...]:
    """Run the official Codex validator once for every generated skill."""
    paths = tuple(sorted(skill_paths, key=lambda path: path.name))
    uv = shutil.which("uv")
    if not uv:
        return tuple(
            OfficialValidation(path.name, False, "uv executable is not available")
            for path in paths
        )
    if not OFFICIAL_VALIDATOR.is_file():
        return tuple(
            OfficialValidation(
                path.name,
                False,
                f"official validator does not exist: {OFFICIAL_VALIDATOR}",
            )
            for path in paths
        )
    results: list[OfficialValidation] = []
    offline = False
    for index, path in enumerate(paths):
        command = [
            uv,
            *OFFICIAL_COMMAND_PREFIX[1:],
            str(OFFICIAL_VALIDATOR),
            str(path),
        ]
        try:
            environment = None
            if offline:
                environment = dict(os.environ)
                environment["UV_OFFLINE"] = "1"
            completed = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=180,
                env=environment,
            )
            output = _normalize_official_output(completed.stdout + completed.stderr)
            normalized_output = output.lower()
            shared_resolution_failure = (
                completed.returncode != 0
                and "failed to fetch" in normalized_output
                and "pyyaml" in normalized_output
                and (
                    "dns error" in normalized_output
                    or "failed to lookup address" in normalized_output
                )
            )
            if shared_resolution_failure and not offline:
                offline_environment = dict(os.environ)
                offline_environment["UV_OFFLINE"] = "1"
                offline_result = subprocess.run(
                    command,
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=180,
                    env=offline_environment,
                )
                offline_output = _normalize_official_output(
                    offline_result.stdout + offline_result.stderr
                )
                if offline_result.returncode == 0:
                    offline = True
                    results.append(
                        OfficialValidation(
                            path.name,
                            True,
                            offline_output,
                            "offline-cached-fallback",
                            _sanitize_official_diagnostic(output),
                        )
                    )
                    continue
                results.append(
                    OfficialValidation(
                        path.name,
                        False,
                        offline_output or output,
                        "offline-fallback-failed",
                        _sanitize_official_diagnostic(output),
                    )
                )
                results.extend(
                    OfficialValidation(
                        remaining.name,
                        False,
                        output,
                        "not-run-after-shared-failure",
                        _sanitize_official_diagnostic(output),
                    )
                    for remaining in paths[index + 1 :]
                )
                break
            results.append(
                OfficialValidation(
                    path.name,
                    completed.returncode == 0,
                    output,
                    "offline-cached" if offline else "online",
                )
            )
        except (OSError, subprocess.SubprocessError) as error:
            results.append(
                OfficialValidation(path.name, False, str(error), "execution-error")
            )
    return tuple(results)


def run_regression_validation(repo_root: Path) -> tuple[RegressionValidation, ...]:
    """Run the full suite in bounded subprocesses without recursively collecting evidence."""
    codex_root = Path(repo_root) / "codex-skills"
    results: list[RegressionValidation] = []
    for executable in _python_executables():
        try:
            version_result = subprocess.run(
                [executable, "--version"],
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )
            interpreter = (
                version_result.stdout + version_result.stderr
            ).strip() or Path(executable).name
            completed = subprocess.run(
                [
                    executable,
                    "-m",
                    "unittest",
                    "discover",
                    "-s",
                    "tests",
                    "-q",
                ],
                cwd=codex_root,
                check=False,
                capture_output=True,
                text=True,
                timeout=600,
            )
            output = completed.stdout + completed.stderr
            match = re.search(r"Ran\s+(\d+)\s+tests?\b", output)
            tests_run = int(match.group(1)) if match else 0
            passed = completed.returncode == 0 and tests_run > 0
            diagnostic = "" if passed else (
                f"exit code {completed.returncode}; observed {tests_run} tests"
            )
            results.append(
                RegressionValidation(interpreter, tests_run, passed, diagnostic)
            )
        except (OSError, subprocess.SubprocessError) as error:
            results.append(
                RegressionValidation(
                    Path(executable).name,
                    0,
                    False,
                    f"regression suite failed to run: {type(error).__name__}",
                )
            )
    return tuple(results)


def _write_injection_skill(root: Path, body: str = "# Sample\n") -> Path:
    skill = root / "sample"
    (skill / "agents").mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        '---\nname: "sample"\ndescription: "Useful validation sample."\n---\n\n'
        + body,
        encoding="utf-8",
    )
    (skill / "agents" / "openai.yaml").write_text(
        "interface:\n"
        '  display_name: "Sample"\n'
        '  short_description: "A useful validation sample."\n'
        '  default_prompt: "Use $sample to validate this fixture."\n',
        encoding="utf-8",
    )
    return skill


def run_injected_defect_validation() -> tuple[InjectedDefectValidation, ...]:
    """Inject representative defects and record whether the real validator detects them."""
    checks: list[InjectedDefectValidation] = []

    def observe(
        category: str,
        name: str,
        configure,
        expected: tuple[str, ...],
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="codex-validator-injection-") as directory:
            skill = _write_injection_skill(Path(directory))
            configure(skill)
            result = validate_skill(skill)
            passed = all(
                any(marker in error for error in result.errors) for marker in expected
            )
            checks.append(
                InjectedDefectValidation(
                    category,
                    name,
                    passed,
                    "" if passed else "expected defect was not detected",
                )
            )

    observe(
        "Claude runtime compatibility",
        "Claude Code session environment",
        lambda skill: (skill / "SKILL.md").write_text(
            '---\nname: "sample"\ndescription: "Useful validation sample."\n---\n\n'
            "Run this workflow only in Claude Code and write to "
            "${CLAUDE_SESSION_ID}.\n",
            encoding="utf-8",
        ),
        ("Claude runtime/client/environment",),
    )
    observe(
        "Claude runtime compatibility",
        "Claude-only tool",
        lambda skill: (skill / "SKILL.md").write_text(
            '---\nname: "sample"\ndescription: "Useful validation sample."\n---\n\n'
            "Use the AskUserQuestion tool now.\n",
            encoding="utf-8",
        ),
        ("AskUserQuestion",),
    )
    observe(
        "frontmatter and metadata",
        "extra frontmatter field",
        lambda skill: (skill / "SKILL.md").write_text(
            '---\nname: "sample"\ndescription: "Useful validation sample."\n'
            "extra: forbidden\n---\n\n# Sample\n",
            encoding="utf-8",
        ),
        ("frontmatter",),
    )
    observe(
        "frontmatter and metadata",
        "missing default prompt token",
        lambda skill: (skill / "agents" / "openai.yaml").write_text(
            "interface:\n"
            '  display_name: "Sample"\n'
            '  short_description: "A useful validation sample."\n'
            '  default_prompt: "Use this fixture."\n',
            encoding="utf-8",
        ),
        ("$sample",),
    )
    observe(
        "local resource integrity",
        "missing inline script",
        lambda skill: (skill / "SKILL.md").write_text(
            '---\nname: "sample"\ndescription: "Useful validation sample."\n---\n\n'
            "Run `scripts/missing.py`.\n",
            encoding="utf-8",
        ),
        ("scripts/missing.py",),
    )
    observe(
        "local resource integrity",
        "broken Markdown link",
        lambda skill: (skill / "SKILL.md").write_text(
            '---\nname: "sample"\ndescription: "Useful validation sample."\n---\n\n'
            "See [missing](references/missing.md).\n",
            encoding="utf-8",
        ),
        ("broken local link",),
    )
    for suffix, content in (
        ("py", "def broken(:\n"),
        ("sh", "if then\n"),
        ("js", "function {\n"),
    ):
        observe(
            "resource syntax",
            f"invalid {suffix} syntax",
            lambda skill, suffix=suffix, content=content: (
                (skill / "scripts").mkdir(),
                (skill / "scripts" / f"bad.{suffix}").write_text(
                    content, encoding="utf-8"
                ),
            ),
            (f"bad.{suffix}",),
        )
    return tuple(checks)


def _dependency_status(entry: SkillEntry) -> DependencyStatus:
    command_aliases = {
        "bash": ("bash",),
        "curl": ("curl",),
        "file": ("file",),
        "gcloud cli": ("gcloud",),
        "cloud-sql-proxy": ("cloud-sql-proxy",),
        "node.js": ("node",),
        "python 3.12 or newer": ("python3.12",),
    }
    credential_markers = (
        "credential",
        "auth",
        "api key",
        "ssh",
        "user and adc access",
        "publishing",
    )
    connector_markers = (
        " mcp",
        "connected ",
        "browser",
        "network",
        "repository",
        "environment",
        "service",
        "deployment",
        "source api",
        "local ",
        "git repository",
        "platform backend",
    )
    probes: list[DependencyProbe] = []
    for dependency in entry.dependencies:
        normalized = dependency.casefold()
        if normalized == "google chrome":
            chrome_paths = (
                Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
                Path("/Applications/Chromium.app/Contents/MacOS/Chromium"),
            )
            available = any(
                shutil.which(command)
                for command in ("google-chrome", "chromium", "chromium-browser")
            ) or any(path.is_file() for path in chrome_paths)
            probe_status = "available" if available else "missing"
        elif normalized in command_aliases:
            available = any(
                shutil.which(command) for command in command_aliases[normalized]
            )
            probe_status = "available" if available else "missing"
        elif any(marker in normalized for marker in credential_markers):
            probe_status = "credential-dependent"
        elif any(marker in normalized for marker in connector_markers):
            probe_status = "connector-dependent"
        else:
            probe_status = "not-probed"
        probes.append(DependencyProbe(dependency, probe_status))

    observed = {probe.status for probe in probes}
    if "missing" in observed:
        status = "missing"
    elif "not-probed" in observed or not probes:
        status = "partial"
    elif "credential-dependent" in observed:
        status = "credential-dependent"
    elif "connector-dependent" in observed:
        status = "connector-dependent"
    else:
        status = "available"
    return DependencyStatus(entry.output, entry.dependencies, status, tuple(probes))


def validate_approved_existing(path: Path, name: str) -> tuple[str, ...]:
    """Validate an approved real directory or unrelated resolved skill symlink."""
    errors: list[str] = []
    try:
        root = path.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        return (f"approved existing skill does not resolve: {error}",)
    if not root.is_dir():
        return ("approved existing skill must resolve to a directory",)
    text, read_error = _read_text(root / "SKILL.md")
    if read_error:
        errors.append(read_error)
    elif text is not None:
        keys = _frontmatter_keys(text)
        if len(keys) != 2 or set(keys) != {"name", "description"}:
            errors.append("SKILL.md frontmatter must contain only name and description")
        try:
            document = parse_skill_document(text)
        except ValueError as error:
            errors.append(f"SKILL.md invalid frontmatter: {error}")
        else:
            if document.name != name:
                errors.append(
                    f"SKILL.md frontmatter name {document.name!r} does not match folder"
                )
    _validate_symlinks(root, errors)
    return tuple(errors)


def _validate_installed(
    installed: Path,
    output_root: Path,
    expected_names: set[str],
    approved_existing: tuple[str, ...],
    exclude: tuple[str, ...],
    errors: list[str],
) -> tuple[int, int, tuple[str, ...]]:
    installed_root = Path(installed).expanduser()
    if installed_root.is_symlink() or not installed_root.is_dir():
        errors.append(f"installed skill root does not exist: {installed_root}")
        return 0, 0, ()
    approved = set(approved_existing)
    requested_exclusions = set(exclude)
    invalid_approvals = sorted(
        name
        for name in approved
        if SAFE_SKILL_NAME.fullmatch(name) is None or name not in expected_names
    )
    if invalid_approvals:
        errors.append(
            "approved existing skill names are invalid or unmanaged: "
            + ", ".join(invalid_approvals)
        )
    invalid_exclusions = sorted(
        name
        for name in requested_exclusions
        if SAFE_SKILL_NAME.fullmatch(name) is None or name not in expected_names
    )
    if invalid_exclusions:
        errors.append(
            "excluded skill names are invalid or unmanaged: "
            + ", ".join(invalid_exclusions)
        )
    conflicting = sorted(approved & requested_exclusions)
    if conflicting:
        errors.append(
            "skill names cannot be both approved and excluded: "
            + ", ".join(conflicting)
        )
    excluded = tuple(sorted(requested_exclusions.intersection(expected_names)))
    managed_count = 0
    approved_count = 0
    for name in sorted(expected_names):
        if name in excluded:
            continue
        path = installed_root / name
        if path.is_symlink():
            try:
                target = path.resolve(strict=True)
            except (FileNotFoundError, RuntimeError) as error:
                errors.append(f"installed skill {name} is a broken link: {error}")
                continue
            if target == (output_root / name).resolve(strict=False):
                managed_count += 1
                continue
            if name not in approved:
                errors.append(f"installed skill {name} links to an unexpected target")
                continue
            validation_errors = validate_approved_existing(path, name)
            if validation_errors:
                errors.extend(
                    f"installed skill {name}: {error}" for error in validation_errors
                )
                continue
            approved_count += 1
            continue
        if name not in approved:
            errors.append(f"installed skill {name} must be a managed symlink")
            continue
        validation_errors = validate_approved_existing(path, name)
        if validation_errors:
            errors.extend(
                f"installed skill {name}: {error}" for error in validation_errors
            )
            continue
        approved_count += 1
    return managed_count, approved_count, excluded


def validate_collection(
    repo_root: Path,
    installed: Path | None = None,
    *,
    approved_existing: tuple[str, ...] = (),
    exclude: tuple[str, ...] = (),
    source_only: bool = False,
    collect_evidence: bool = False,
    structural_only: bool = False,
) -> CollectionReport:
    """Validate protected inputs and, unless source-only, all generated outputs."""
    root = Path(repo_root).expanduser().resolve(strict=False)
    errors: list[str] = []
    warnings: list[str] = []
    installed_only_inputs = tuple(
        name
        for name, present in (
            ("installed", installed is not None),
            ("approved-existing", bool(approved_existing)),
            ("exclude", bool(exclude)),
        )
        if present
    )
    if source_only and installed_only_inputs:
        errors.append(
            "source-only validation cannot be combined with installed-only inputs: "
            + ", ".join(installed_only_inputs)
        )
    elif exclude and installed is None:
        errors.append("excluded skill names require an installed skill root")
    if structural_only and collect_evidence:
        errors.append(
            "full evidence was requested but suppressed by structural-only validation"
        )
    source_hash_count, source_hashes_match, source_errors = _validate_source_hashes(root)
    errors.extend(source_errors)
    manifest: Manifest | None = None
    class_counts: tuple[tuple[str, int], ...] = ()
    try:
        manifest = load_manifest(
            root / "codex-skills" / "manifest.yaml", repo_root=root
        )
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as error:
        errors.append(f"manifest validation failed: {error}")
    else:
        class_counts = _validate_manifest_contract(manifest, errors)

    if source_only:
        return CollectionReport(
            repo_root=root,
            generated_on=date.today().isoformat(),
            skill_results=(),
            errors=tuple(errors),
            warnings=tuple(warnings),
            class_counts=class_counts,
            source_hash_count=source_hash_count,
            source_hashes_match=source_hashes_match,
            markdown_count=0,
            resource_count=0,
            runtime_count=0,
            native_runtime_absent_count=0,
            dependency_preflight_count=0,
            dependency_secret_count=0,
            syntax_results=(),
            official_results=(),
            dependency_statuses=(),
            installed_count=None,
            source_only=True,
            structural_fingerprint=_structural_fingerprint(root),
        )

    output_root = root / "codex-skills" / "skills"
    actual_names: set[str] = set()
    if output_root.is_symlink() or not output_root.is_dir():
        errors.append(f"generated output root is missing or unsafe: {output_root}")
    else:
        actual_names = {
            path.name for path in output_root.iterdir() if path.is_dir() and not path.is_symlink()
        }
        root_extras = sorted(
            path.name
            for path in output_root.iterdir()
            if not path.is_dir() and path.name != GENERATED_MARKER
        )
        if root_extras:
            errors.append("extra files at generated output root: " + ", ".join(root_extras))
    if len(actual_names) != EXPECTED_SKILL_COUNT:
        errors.append(
            f"generated output must contain exactly {EXPECTED_SKILL_COUNT} skill folders, "
            f"found {len(actual_names)}"
        )
    expected_names = {entry.output for entry in manifest.entries} if manifest else set()
    missing_names = sorted(expected_names - actual_names)
    extra_names = sorted(actual_names - expected_names)
    if missing_names:
        errors.append("missing output skill folders: " + ", ".join(missing_names))
    if extra_names:
        errors.append("extra output skill folders: " + ", ".join(extra_names))

    skill_results = tuple(
        validate_skill(output_root / name, run_syntax=not structural_only)
        for name in sorted(actual_names)
    )
    for result in skill_results:
        errors.extend(f"{result.name}: {error}" for error in result.errors)
        warnings.extend(f"{result.name}: {warning}" for warning in result.warnings)
    syntax_results = tuple(
        syntax
        for result in skill_results
        for syntax in result.syntax_results
        if syntax.paths or syntax.errors
    )

    runtime_count = 0
    native_absent = 0
    dependency_preflight = 0
    dependency_secret = 0
    dependency_statuses: tuple[DependencyStatus, ...] = ()
    if manifest is not None and output_root.is_dir():
        (
            runtime_count,
            native_absent,
            dependency_preflight,
            dependency_secret,
        ) = _validate_runtime_contracts(manifest, output_root, errors)
        if not structural_only:
            dependency_statuses = tuple(
                _dependency_status(entry)
                for entry in sorted(manifest.entries, key=lambda item: item.output)
                if entry.conversion == "dependency-required"
            )
        _validate_expected_parity(root, manifest, output_root, errors)

    skill_paths = tuple(output_root / name for name in sorted(actual_names))
    official_results: tuple[OfficialValidation, ...] = ()
    if not structural_only:
        official_results = run_official_validation(skill_paths)
        if len(official_results) != EXPECTED_SKILL_COUNT:
            errors.append(
                f"official validator must return {EXPECTED_SKILL_COUNT} results, "
                f"found {len(official_results)}"
            )
        official_failures = tuple(
            result for result in official_results if not result.passed
        )
        distinct_official_failures = {result.output for result in official_failures}
        if (
            len(official_failures) > 1
            and len(distinct_official_failures) == 1
            and "failed to fetch" in next(iter(distinct_official_failures), "").lower()
        ):
            detail = next(iter(distinct_official_failures)) or "no diagnostic output"
            errors.append(
                f"official validator blocked for all {len(official_failures)} skills by "
                f"shared uv dependency resolution: {detail}"
            )
        else:
            for result in official_failures:
                detail = result.output or "no diagnostic output"
                errors.append(f"{result.name}: official validator failed: {detail}")

    installed_count: int | None = None
    approved_existing_count: int | None = None
    excluded: tuple[str, ...] = ()
    if installed is not None:
        installed_count, approved_existing_count, excluded = _validate_installed(
            Path(installed),
            output_root,
            expected_names,
            approved_existing,
            exclude,
            errors,
        )

    regression_results: tuple[RegressionValidation, ...] = ()
    injected_defect_results: tuple[InjectedDefectValidation, ...] = ()
    evidence_required = (
        manifest is not None
        and len(manifest.entries) == EXPECTED_SKILL_COUNT
        and len(actual_names) == EXPECTED_SKILL_COUNT
    )
    if evidence_required and collect_evidence and not structural_only:
        regression_results = run_regression_validation(root)
        injected_defect_results = run_injected_defect_validation()
        if not regression_results:
            errors.append("full regression suite evidence is missing")
        for result in regression_results:
            if not result.passed:
                errors.append(
                    f"regression suite failed under {result.interpreter}: "
                    f"{result.diagnostic}"
                )
        if not injected_defect_results:
            errors.append("injected defect validation evidence is missing")
        for result in injected_defect_results:
            if not result.passed:
                errors.append(
                    f"injected defect was not detected ({result.category}/"
                    f"{result.name}): {result.diagnostic}"
                )

    markdown_count = sum(result.markdown_count for result in skill_results)
    resource_count = 0
    if output_root.is_dir():
        resource_count = sum(path.is_file() for path in output_root.rglob("*"))
    return CollectionReport(
        repo_root=root,
        generated_on=date.today().isoformat(),
        skill_results=skill_results,
        errors=tuple(errors),
        warnings=tuple(warnings),
        class_counts=class_counts,
        source_hash_count=source_hash_count,
        source_hashes_match=source_hashes_match,
        markdown_count=markdown_count,
        resource_count=resource_count,
        runtime_count=runtime_count,
        native_runtime_absent_count=native_absent,
        dependency_preflight_count=dependency_preflight,
        dependency_secret_count=dependency_secret,
        syntax_results=syntax_results,
        official_results=official_results,
        dependency_statuses=dependency_statuses,
        installed_count=installed_count,
        source_only=False,
        approved_existing_count=approved_existing_count,
        excluded=excluded,
        structural_fingerprint=_structural_fingerprint(root),
        regression_results=regression_results,
        injected_defect_results=injected_defect_results,
    )


def _syntax_summary(report: CollectionReport) -> tuple[dict[str, set[str]], dict[str, int]]:
    interpreters: dict[str, set[str]] = {}
    paths: dict[str, set[str]] = {}
    for skill in report.skill_results:
        for result in skill.syntax_results:
            interpreters.setdefault(result.language, set()).add(result.interpreter)
            language_paths = paths.setdefault(result.language, set())
            language_paths.update(f"{skill.name}/{path}" for path in result.paths)
    return interpreters, {language: len(items) for language, items in paths.items()}


def _snapshot_digest(repo_root: Path) -> str:
    path = repo_root / "codex-skills" / "source-hashes.json"
    try:
        return sha256(path.read_bytes()).hexdigest()
    except OSError:
        return "unavailable"


def render_report(report: CollectionReport) -> str:
    """Render a deterministic Markdown report from observed validation results."""
    classes = dict(report.class_counts)
    interpreters, syntax_counts = _syntax_summary(report)
    status = "PASS" if report.ok else "FAIL"
    local_status = "PASS" if not any(
        "official validator" not in error for error in report.errors
    ) else "FAIL"
    regression_status = (
        "NOT OBSERVED"
        if not report.regression_results
        else "PASS"
        if all(result.passed for result in report.regression_results)
        else "FAIL"
    )
    injection_status = (
        "NOT OBSERVED"
        if not report.injected_defect_results
        else "PASS"
        if all(result.passed for result in report.injected_defect_results)
        else "FAIL"
    )
    injection_passes = sum(
        result.passed for result in report.injected_defect_results
    )
    injection_total = len(report.injected_defect_results)
    excluded_summary = f"{report.excluded_count} excluded"
    if report.excluded:
        excluded_summary += " (" + ", ".join(
            f"`{name}`" for name in report.excluded
        ) + ")"
    lines = [
        "# Codex Skills Validation",
        "",
        f"- **Observed date:** {report.generated_on}",
        f"- **Structural fingerprint:** `{report.structural_fingerprint}`",
        f"- **Overall:** {status}",
        f"- **Collection:** {report.skill_count} total; "
        f"{classes.get('native', 0)} native; {classes.get('adapted', 0)} adapted; "
        f"{classes.get('dependency-required', 0)} dependency-required",
        f"- **Protected sources:** {'PASS' if report.source_hashes_match else 'FAIL'}; "
        f"{report.source_hash_count} files; snapshot SHA-256 "
        f"`{_snapshot_digest(report.repo_root)}`",
        f"- **Generated resources:** {report.markdown_count} Markdown; "
        f"{report.resource_count} total files",
        f"- **Runtime contracts:** {report.runtime_count} sections; "
        f"{report.native_runtime_absent_count} native absences; "
        f"{report.dependency_preflight_count} dependency preflights; "
        f"{report.dependency_secret_count} no-secret clauses",
        f"- **Official validator:** {report.official_passes}/{len(report.official_results)} passed",
        f"- **Regression suites:** **{regression_status}**",
        (
            f"- **Injected defect checks:** **{injection_status}**; "
            f"{injection_passes}/{injection_total} detected"
            if report.injected_defect_results
            else f"- **Injected defect checks:** **{injection_status}**"
        ),
        (
            f"- **Installability:** {report.installed_count} managed links; "
            f"{report.approved_existing_count or 0} approved existing directories; "
            f"{excluded_summary}; "
            f"{(report.installed_count or 0) + (report.approved_existing_count or 0) + report.excluded_count}/"
            f"{report.skill_count} generated names accounted for"
            if report.installed_count is not None
            else "- **Installability:** generated names and resources validated; personal "
            "installation not inspected"
        ),
        "",
        "## Schema, Metadata, Runtime, and Resources",
        "",
        f"Structural/schema validation: **{local_status}**. Metadata, normalized output parity, "
        "Markdown compatibility, local links, symlink containment, helper overlays, "
        "resource modes, and runtime contracts were checked from generated files.",
        "",
        "## Official Validator Execution",
        "",
    ]
    if report.official_results:
        mode_counts: dict[str, int] = {}
        for result in report.official_results:
            mode_counts[result.execution_mode] = (
                mode_counts.get(result.execution_mode, 0) + 1
            )
        lines.append(
            "Observed execution modes: "
            + ", ".join(
                f"`{mode}` {count}" for mode, count in sorted(mode_counts.items())
            )
            + "."
        )
        diagnostics = tuple(
            dict.fromkeys(
                result.initial_diagnostic
                for result in report.official_results
                if result.initial_diagnostic
            )
        )
        if diagnostics:
            lines.append(
                "Initial online diagnostic (sanitized): " + "; ".join(diagnostics) + "."
            )
            lines.append(
                "Fallback evidence: online dependency resolution failed, then the cached "
                f"`UV_OFFLINE=1` environment validated {report.official_passes}/"
                f"{len(report.official_results)} skills."
            )
    else:
        lines.append("Official validator execution was not observed.")
    lines.extend(["", "## Regression and Injection Evidence", ""])
    if report.regression_results:
        lines.extend(
            [
                "| Interpreter | Observed tests | Result |",
                "|---|---:|---|",
            ]
        )
        for result in report.regression_results:
            result_text = "PASS" if result.passed else "FAIL"
            lines.append(
                f"| {result.interpreter} | {result.tests_run}/{result.tests_run} | "
                f"{result_text} |"
            )
    else:
        lines.append("Regression suites: **NOT OBSERVED**.")
    lines.append("")
    if report.injected_defect_results:
        lines.extend(
            [
                "| Injected defect category | Exact injected defect | Detection | Result |",
                "|---|---|---|---|",
            ]
        )
        for result in report.injected_defect_results:
            detection = "detected" if result.passed else "not detected"
            result_text = "PASS" if result.passed else "FAIL"
            lines.append(
                f"| {result.category} | `{result.name}` | {detection} | "
                f"{result_text} |"
            )
    else:
        lines.append("Injected defect checks: **NOT OBSERVED**.")
    lines.extend(
        [
            "",
            "## Syntax Checks",
            "",
            "| Language | Observed files | Interpreters | Result |",
            "|---|---:|---|---|",
        ]
    )
    for language in ("python", "shell", "javascript"):
        runtimes = sorted(interpreters.get(language, {"not available"}))
        relevant = [result for result in report.syntax_results if result.language == language]
        failures = sum(len(result.errors) for result in relevant)
        result_text = "PASS" if failures == 0 else f"FAIL ({failures})"
        lines.append(
            f"| {language} | {syntax_counts.get(language, 0)} | "
            f"{'<br>'.join(runtimes)} | {result_text} |"
        )
    lines.extend(
        [
            "",
            "Python resources were compiled with the default `python3` and Python 3.11 "
            "when available. Shell resources used `bash -n`; JavaScript resources used "
            "`node --check` when Node was available. Fixtures, caches, vendored trees, "
            "and build outputs were excluded.",
            "",
            "## Immediately Usable and Adapted",
            "",
            "The native and adapted skills below have no mandatory external dependency "
            "contract in the manifest:",
            "",
        ]
    )
    dependency_names = {item.name for item in report.dependency_statuses}
    immediate = sorted(
        result.name
        for result in report.skill_results
        if result.name not in dependency_names
    )
    lines.append(", ".join(f"`{name}`" for name in immediate) or "None observed.")
    lines.extend(
        [
            "",
            "## Dependency-Gated Skills",
            "",
            "Statuses are non-secret observations only. Connector-dependent does "
            "not claim that a connector is available.",
            "",
            "| Skill | Exact mandatory dependencies | Observed preflight status |",
            "|---|---|---|",
        ]
    )
    for item in report.dependency_statuses:
        dependencies = "<br>".join(
            f"`{probe.dependency}` ({probe.status})" for probe in item.probes
        )
        lines.append(f"| `{item.name}` | {dependencies} | {item.status} |")
    lines.extend(
        [
            "",
            "## Limitations",
            "",
            "No live external workflows, external services, credentials, production "
            "commands, or user media were executed. Availability checks do not expose "
            "credential values and do not prove live connector authorization.",
        ]
    )
    if report.errors:
        lines.extend(["", "## Errors", ""])
        lines.extend(f"- {error}" for error in report.errors)
    if report.warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in report.warnings)
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    default_repo = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description="Validate generated Codex skills.")
    parser.add_argument("--repo", type=Path, default=default_repo)
    parser.add_argument("--installed", type=Path)
    parser.add_argument("--approved-existing", action="append", default=[])
    parser.add_argument("--exclude", action="append", default=[])
    parser.add_argument("--source-only", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--test-child", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.source_only and args.check:
        parser.error("--source-only cannot be combined with --check")
    if args.source_only and (
        args.installed is not None or args.approved_existing or args.exclude
    ):
        parser.error(
            "--source-only cannot be combined with --installed, "
            "--approved-existing, or --exclude"
        )
    if args.test_child and (args.source_only or args.check):
        parser.error("--test-child cannot be combined with --source-only or --check")
    if args.approved_existing and args.installed is None:
        parser.error("--approved-existing requires --installed")
    if args.exclude and args.installed is None:
        parser.error("--exclude requires --installed")

    report = validate_collection(
        args.repo,
        installed=args.installed,
        approved_existing=tuple(args.approved_existing),
        exclude=tuple(args.exclude),
        source_only=args.source_only,
        collect_evidence=not args.source_only and not args.check and not args.test_child,
        structural_only=args.check,
    )
    evidence_requested = not args.source_only and not args.check and not args.test_child
    if evidence_requested:
        missing_evidence: list[str] = []
        if not report.regression_results:
            missing_evidence.append("requested full report regression evidence is missing")
        if not report.injected_defect_results:
            missing_evidence.append(
                "requested full report injected defect evidence is missing"
            )
        if missing_evidence:
            report = replace(
                report,
                errors=report.errors
                + tuple(
                    error for error in missing_evidence if error not in report.errors
                ),
            )
    rendered = render_report(report)
    report_path = args.repo / "codex-skills" / "VALIDATION.md"
    report_current = True
    if args.check:
        try:
            committed = report_path.read_text(encoding="utf-8")
            match = REPORT_FINGERPRINT.search(committed)
            report_current = bool(
                match
                and report.structural_fingerprint
                and match.group(1) == report.structural_fingerprint
            )
        except OSError:
            report_current = False
    elif not args.json and not args.source_only and not args.test_child:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with report_path.open("w", encoding="utf-8", newline="") as output:
            output.write(rendered)

    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(
            f"Validated {report.skill_count} skills: "
            f"{len(report.errors)} error(s), {len(report.warnings)} warning(s)."
        )
        for error in report.errors:
            print(f"Error: {error}", file=sys.stderr)
        if args.check and not report_current:
            print(f"Error: committed validation report is stale: {report_path}", file=sys.stderr)
    return 0 if report.ok and report_current else 1


if __name__ == "__main__":
    raise SystemExit(main())
