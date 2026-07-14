#!/usr/bin/env python3

import argparse
import json
import os
import re
import shutil
import stat
import sys
import tempfile
from dataclasses import dataclass, replace
from hashlib import sha256
from pathlib import Path

try:
    from scripts.adapt import (
        adapt_description,
        adapt_text,
        is_adapted_resource,
        validate_generated_markdown,
    )
    from scripts.common import (
        SAFE_SKILL_NAME,
        Manifest,
        SkillDocument,
        SkillEntry,
        load_manifest,
        parse_skill_document,
        render_skill_document,
    )
except ModuleNotFoundError:  # Support direct execution as scripts/build.py.
    from adapt import (  # type: ignore[no-redef]
        adapt_description,
        adapt_text,
        is_adapted_resource,
        validate_generated_markdown,
    )
    from common import (  # type: ignore[no-redef]
        SAFE_SKILL_NAME,
        Manifest,
        SkillDocument,
        SkillEntry,
        load_manifest,
        parse_skill_document,
        render_skill_document,
    )


EXCLUDED_DIRECTORIES = {
    ".git",
    ".cache",
    ".gstack",
    ".herenow",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "cache",
    "logs",
    "runtime",
}
EXCLUDED_FILENAMES = {".DS_Store"}
GENERATED_MARKER = ".codex-skills-generated"
GENERATED_ADAPTER_RESOURCES = {
    "context-keeper": (
        (
            Path("codex-skills/adapters/context-keeper/new-session.sh"),
            Path("scripts/new-session.sh"),
        ),
    ),
    "skill-miner": (
        (
            Path("codex-skills/adapters/skill-miner/digest_codex.py"),
            Path("scripts/digest_codex.py"),
        ),
    ),
    "skills-librarian": (
        (
            Path("codex-skills/adapters/skills-librarian/audit.py"),
            Path("scripts/audit.py"),
        ),
    ),
}
REQUIRED_OVERRIDE_NAMES = frozenset(
    {
        "context-keeper",
        "doc-keeper",
        "gws-shared",
        "gws-workflow",
        "gws-workflow-email-to-task",
        "gws-workflow-file-announce",
        "gws-workflow-meeting-prep",
        "gws-workflow-standup-report",
        "gws-workflow-weekly-digest",
        "page-rethink",
        "skill-miner",
        "skills-librarian",
        "tiger-doc-keeper",
    }
)
AUDIT_PROMOTED_PROVENANCE = {
    "assumptions-audit": ".agents-backup/gsd-assumptions-analyzer.md",
    "codebase-pattern-mapping": ".agents-backup/gsd-pattern-mapper.md",
    "documentation-claim-verification": ".agents-backup/gsd-doc-verifier.md",
    "integration-flow-audit": ".agents-backup/gsd-integration-checker.md",
    "requirements-coverage-audit": ".agents-backup/gsd-nyquist-auditor.md",
    "threat-mitigation-audit": ".agents-backup/gsd-security-auditor.md",
    "ai-evaluation-audit": ".agents-backup/gsd-eval-auditor.md",
}
LEGACY_PROMOTED_PROVENANCE = {
    name: f"codex-skills/archived-sources/{name}/SKILL.md"
    for name in (
        "gitnexus-cli",
        "gitnexus-debugging",
        "gitnexus-exploring",
        "gitnexus-guide",
        "gitnexus-impact-analysis",
        "gitnexus-pr-review",
        "gitnexus-refactoring",
    )
}
PROMOTED_PROVENANCE = {
    **AUDIT_PROMOTED_PROVENANCE,
    **LEGACY_PROMOTED_PROVENANCE,
}
OVERRIDE_REQUIRED_SECTIONS = (
    "## Codex Runtime",
    "## Inputs and Preflight",
    "## Procedure",
    "## Safety and Errors",
    "## Output Contract",
)
_MANDATORY_DELEGATION = re.compile(
    r"\b(?:must|required to|always)\s+(?:delegate|use (?:a )?subagent)",
    re.IGNORECASE,
)
_PROMOTED_ARCHIVED_RUNTIME = re.compile(
    r"(?:\bgsd\b|\.planning/|\.claude/|\borchestrator\b|\bslash command\b)",
    re.IGNORECASE,
)
PROMOTED_SECRET_CLAUSE = "Never expose or print secret, credential, or token values."
PROMOTED_PREFLIGHT_CLAUSE = "Preflight each dependency using MCP/app capability discovery"
PROMOTED_BLOCKED_CLAUSE = "If any mandatory dependency is unavailable"


@dataclass(frozen=True)
class BuildResult:
    output_dir: Path
    built_names: tuple[str, ...]
    warnings: tuple[str, ...] = ()

    @property
    def count(self) -> int:
        return len(self.built_names)


@dataclass(frozen=True)
class TreeEntry:
    kind: str
    mode: int
    payload: str = ""


@dataclass(frozen=True)
class BuildCheckResult:
    output_dir: Path
    missing_paths: tuple[str, ...] = ()
    extra_paths: tuple[str, ...] = ()
    changed_paths: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return not (
            self.errors
            or self.missing_paths
            or self.extra_paths
            or self.changed_paths
        )

    @property
    def diagnostics(self) -> tuple[str, ...]:
        diagnostics = list(self.errors)
        for label, paths in (
            ("missing paths", self.missing_paths),
            ("extra paths", self.extra_paths),
            ("changed paths", self.changed_paths),
        ):
            if paths:
                diagnostics.append(f"{label}: {', '.join(paths)}")
        return tuple(diagnostics)


@dataclass(frozen=True)
class _ValidatedSource:
    entry: SkillEntry
    source_dir: Path
    document: SkillDocument
    resources: tuple[Path, ...]


@dataclass(frozen=True)
class _ValidatedPromoted:
    entry: SkillEntry
    source_dir: Path
    document: SkillDocument
    resources: tuple[Path, ...]


def _is_relative_to(path: Path, parent: Path) -> bool:
    return path == parent or path.is_relative_to(parent)


def _validate_output_path(
    repo_root: Path, protected_paths: list[Path], output_dir: Path
) -> Path:
    expanded_output = output_dir.expanduser()
    if expanded_output.is_symlink():
        raise ValueError(f"unsafe output path is a symlink: {expanded_output}")
    resolved_output = expanded_output.resolve(strict=False)
    if resolved_output == repo_root or repo_root.is_relative_to(resolved_output):
        raise ValueError(f"unsafe output path overlaps repository root: {output_dir}")
    canonical_output = (repo_root / "codex-skills" / "skills").resolve(strict=False)
    is_canonical = resolved_output == canonical_output
    if resolved_output.is_relative_to(repo_root) and not is_canonical:
        raise ValueError(
            f"unsafe output: in-repository output must use canonical path {canonical_output}"
        )
    for protected_path in protected_paths:
        if _is_relative_to(resolved_output, protected_path) or _is_relative_to(
            protected_path, resolved_output
        ):
            raise ValueError(f"unsafe output path overlaps protected input: {output_dir}")
    if resolved_output.exists() and not resolved_output.is_dir():
        raise ValueError(f"unsafe output path is not a directory: {output_dir}")
    if resolved_output.is_dir():
        contents = list(resolved_output.iterdir())
        marker = resolved_output / GENERATED_MARKER
        is_owned = marker.is_file() and not marker.is_symlink()
        if contents and not is_owned:
            raise ValueError(f"output is not builder-owned: {output_dir}")
    return resolved_output


def _is_excluded_file(relative: Path) -> bool:
    if relative == Path("SKILL.md"):
        return True
    if relative == Path("agents/openai.yaml"):
        return True
    name = relative.name
    return (
        name in EXCLUDED_FILENAMES
        or name.endswith(".pyc")
        or name.endswith(".log")
    )


def _validate_symlink(path: Path, source_dir: Path) -> None:
    if Path(os.readlink(path)).is_absolute():
        raise ValueError(
            f"unsafe symlink (absolute symlink target) in {source_dir.name}: {path}"
        )
    try:
        target = path.resolve(strict=True)
    except (FileNotFoundError, RuntimeError) as error:
        raise ValueError(f"unsafe symlink in {source_dir.name}: {path}") from error
    if not target.is_relative_to(source_dir):
        raise ValueError(f"unsafe symlink escapes {source_dir.name}: {path}")


def _collect_resources(source_dir: Path) -> tuple[Path, ...]:
    resources: list[Path] = []
    for current, directory_names, file_names in os.walk(source_dir, topdown=True):
        current_path = Path(current)
        kept_directories: list[str] = []
        for name in sorted(directory_names):
            path = current_path / name
            if name in EXCLUDED_DIRECTORIES:
                continue
            if path.is_symlink():
                _validate_symlink(path, source_dir)
                resources.append(path)
            else:
                kept_directories.append(name)
                resources.append(path)
        directory_names[:] = kept_directories

        for name in sorted(file_names):
            path = current_path / name
            relative = path.relative_to(source_dir)
            if _is_excluded_file(relative):
                continue
            if path.is_symlink():
                _validate_symlink(path, source_dir)
            resources.append(path)
    collected = tuple(
        sorted(resources, key=lambda path: path.relative_to(source_dir).as_posix())
    )
    included_targets = {
        path.relative_to(source_dir) for path in collected if not path.is_symlink()
    }
    for path in collected:
        if not path.is_symlink():
            continue
        target_relative = path.resolve(strict=True).relative_to(source_dir)
        if target_relative not in included_targets:
            raise ValueError(
                f"unsafe symlink target is excluded from {source_dir.name}: {path}"
            )
    return collected


def _display_name(output_name: str) -> str:
    return " ".join(word.capitalize() for word in output_name.split("-"))


def _short_description(description: str, display_name: str) -> str:
    normalized = re.sub(r"\s+", " ", description).strip()
    first_sentence = re.split(r"(?<=[.!?])\s+", normalized, maxsplit=1)[0]
    if len(first_sentence) < 25:
        first_sentence = f"{first_sentence.rstrip('.')} with {display_name}."
    if len(first_sentence) <= 64:
        return first_sentence
    shortened = first_sentence[:61].rsplit(" ", 1)[0].rstrip(".,;:")
    if not shortened:
        shortened = first_sentence[:61]
    return shortened + "..."


def _metadata(entry: SkillEntry, description: str) -> str:
    display_name = _display_name(entry.output)
    interface = {
        "display_name": display_name,
        "short_description": _short_description(description, display_name),
        "default_prompt": (
            f"Use ${entry.output} to handle this request using its documented workflow."
        ),
    }
    lines = ["interface:"]
    lines.extend(
        f"  {key}: {json.dumps(value, ensure_ascii=True)}"
        for key, value in interface.items()
    )
    return "\n".join(lines) + "\n"


def _write_text_exact(path: Path, content: str) -> None:
    with path.open("w", encoding="utf-8", newline="") as output_file:
        output_file.write(content)


def _validate_sources(repo_root: Path, manifest: Manifest) -> list[_ValidatedSource]:
    validated: list[_ValidatedSource] = []
    for entry in sorted(manifest.sources, key=lambda item: item.output):
        if entry.source is None or SAFE_SKILL_NAME.fullmatch(entry.source) is None:
            raise ValueError(f"unsafe source name: {entry.source!r}")
        if SAFE_SKILL_NAME.fullmatch(entry.output) is None:
            raise ValueError(f"unsafe output name: {entry.output!r}")
        source_dir = (repo_root / entry.source).resolve(strict=True)
        if not source_dir.is_relative_to(repo_root) or not source_dir.is_dir():
            raise ValueError(f"unsafe source path: {entry.source}")
        skill_path = source_dir / "SKILL.md"
        if not skill_path.is_file():
            raise ValueError(f"source SKILL.md does not exist: {entry.source}")
        if skill_path.is_symlink():
            _validate_symlink(skill_path, source_dir)
        with skill_path.open("r", encoding="utf-8", newline="") as source_file:
            document = parse_skill_document(source_file.read())
        if document.name != source_dir.name or document.name != entry.source:
            raise ValueError(
                f"source skill name {document.name!r} does not match folder/manifest "
                f"name {entry.source!r}"
            )
        validated.append(
            _ValidatedSource(
                entry=entry,
                source_dir=source_dir,
                document=document,
                resources=_collect_resources(source_dir),
            )
        )
    return validated


def _frontmatter_keys(text: str) -> tuple[str, ...]:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
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


def _promoted_dependency_list(body: str) -> tuple[str, ...]:
    lines = body.splitlines()
    try:
        start = lines.index("Mandatory dependencies:") + 1
    except ValueError:
        return ()
    dependencies: list[str] = []
    for line in lines[start:]:
        if not line.startswith("- `") or not line.endswith("`"):
            break
        dependencies.append(line[3:-1])
    return tuple(dependencies)


def _validate_promoted(
    repo_root: Path, manifest: Manifest
) -> list[_ValidatedPromoted]:
    promoted_root = repo_root / "codex-skills" / "promoted"
    expected_outputs = {entry.output for entry in manifest.promoted}
    declared_outputs = set(expected_outputs)
    canonical_manifest_path = repo_root / "codex-skills" / "manifest.yaml"
    if canonical_manifest_path.is_file() and not canonical_manifest_path.is_symlink():
        canonical_manifest = load_manifest(
            canonical_manifest_path, repo_root=repo_root
        )
        declared_outputs.update(
            entry.output for entry in canonical_manifest.promoted
        )

    if promoted_root.exists():
        if promoted_root.is_symlink() or not promoted_root.is_dir():
            raise ValueError(f"unsafe promoted input root: {promoted_root}")
        actual_outputs = {path.name for path in promoted_root.iterdir()}
    else:
        actual_outputs = set()

    unknown = actual_outputs - declared_outputs
    if unknown:
        raise ValueError(
            "unknown promoted input(s): " + ", ".join(sorted(unknown))
        )

    validated: list[_ValidatedPromoted] = []
    for entry in sorted(manifest.promoted, key=lambda item: item.output):
        if SAFE_SKILL_NAME.fullmatch(entry.output) is None:
            raise ValueError(f"unsafe promoted output name: {entry.output!r}")
        expected_provenance = PROMOTED_PROVENANCE.get(entry.output)
        if expected_provenance is None:
            raise ValueError(f"unknown promoted output: {entry.output}")
        if entry.promoted_from != expected_provenance:
            raise ValueError(
                f"promoted provenance mismatch for {entry.output}: "
                f"expected {expected_provenance!r}, got {entry.promoted_from!r}"
            )
        if entry.source is not None:
            raise ValueError(f"promoted entry {entry.output} must not set source")
        is_legacy = entry.output in LEGACY_PROMOTED_PROVENANCE
        if is_legacy:
            if entry.conversion != "dependency-required" or not entry.dependencies:
                raise ValueError(
                    f"legacy promoted entry {entry.output} must use a "
                    "dependency-required contract"
                )
        elif entry.conversion != "adapted" or entry.dependencies:
            raise ValueError(
                f"audit promoted entry {entry.output} must use adapted conversion "
                "with no dependency contract"
            )

        provenance_candidate = repo_root / expected_provenance
        try:
            provenance = provenance_candidate.resolve(strict=True)
        except (FileNotFoundError, RuntimeError) as error:
            raise ValueError(
                f"promoted provenance does not exist: {expected_provenance}"
            ) from error
        if not provenance.is_relative_to(repo_root) or not provenance.is_file():
            raise ValueError(
                f"unsafe promoted provenance for {entry.output}: {expected_provenance}"
            )

        source_candidate = promoted_root / entry.output
        if not source_candidate.exists():
            raise ValueError(
                f"promoted input does not exist: codex-skills/promoted/{entry.output}"
            )
        if source_candidate.is_symlink():
            raise ValueError(f"unsafe promoted input directory: {entry.output}")
        source_dir = source_candidate.resolve(strict=True)
        if not source_dir.is_relative_to(promoted_root) or not source_dir.is_dir():
            raise ValueError(f"unsafe promoted input directory: {entry.output}")

        skill_path = source_dir / "SKILL.md"
        if not skill_path.is_file():
            raise ValueError(f"promoted input SKILL.md does not exist: {entry.output}")
        if skill_path.is_symlink():
            _validate_symlink(skill_path, source_dir)
        try:
            with skill_path.open("r", encoding="utf-8", newline="") as skill_file:
                text = skill_file.read()
            document = parse_skill_document(text)
        except (OSError, UnicodeError, ValueError) as error:
            raise ValueError(
                f"promoted input {entry.output} is malformed: {error}"
            ) from error

        if _frontmatter_keys(text) != ("name", "description"):
            raise ValueError(
                f"promoted input {entry.output} frontmatter may contain "
                "only name and description"
            )
        if document.name != source_dir.name or document.name != entry.output:
            raise ValueError(
                f"promoted skill name {document.name!r} does not match "
                f"folder/manifest name {entry.output!r}"
            )
        if not document.description.startswith("Use when "):
            raise ValueError(
                f"promoted description for {entry.output} must start with 'Use when '"
            )
        if document.body.count("## Codex Runtime") != 1:
            raise ValueError(
                f"promoted input {entry.output} must contain exactly one "
                "'## Codex Runtime' section"
            )
        if not is_legacy and "main Codex agent" not in document.body:
            raise ValueError(
                f"promoted input {entry.output} must operate in the main Codex agent"
            )
        if is_legacy:
            observed_dependencies = _promoted_dependency_list(document.body)
            if observed_dependencies != entry.dependencies:
                raise ValueError(
                    f"legacy promoted input {entry.output} dependency contract does not "
                    f"match manifest: expected {entry.dependencies!r}, "
                    f"found {observed_dependencies!r}"
                )
            required_clauses = {
                "secret-safety": PROMOTED_SECRET_CLAUSE,
                "preflight": PROMOTED_PREFLIGHT_CLAUSE,
                "blocked-state": PROMOTED_BLOCKED_CLAUSE,
            }
            missing_clauses = [
                label
                for label, clause in required_clauses.items()
                if clause not in document.body
            ]
            if missing_clauses:
                raise ValueError(
                    f"legacy promoted input {entry.output} is missing required "
                    f"runtime clauses: {', '.join(missing_clauses)}"
                )
        elif "Never print, log, or expose secret values." not in document.body:
            raise ValueError(
                f"promoted input {entry.output} is missing the secret-safety clause"
            )
        if _MANDATORY_DELEGATION.search(document.body):
            raise ValueError(
                f"promoted input {entry.output} requires unsupported delegation"
            )
        if _PROMOTED_ARCHIVED_RUNTIME.search(document.body):
            raise ValueError(
                f"promoted input {entry.output} contains archived runtime coupling"
            )
        rendered = render_skill_document(document)
        validate_generated_markdown(entry.output, "SKILL.md", rendered)
        resources = _collect_resources(source_dir)
        for path in resources:
            if path.is_dir() or path.is_symlink() or path.suffix.lower() != ".md":
                continue
            with path.open("r", encoding="utf-8", newline="") as resource_file:
                validate_generated_markdown(
                    entry.output,
                    path.relative_to(source_dir).as_posix(),
                    resource_file.read(),
                )
        validated.append(
            _ValidatedPromoted(
                entry=entry,
                source_dir=source_dir,
                document=document,
                resources=resources,
            )
        )
    return validated


def _normalize_override_document(document: SkillDocument) -> SkillDocument:
    return replace(
        document,
        body=document.body.replace("\r\n", "\n").replace("\r", "\n"),
    )


def _validate_overrides(
    repo_root: Path,
    manifest: Manifest,
    sources: list[_ValidatedSource],
) -> dict[str, SkillDocument]:
    override_root = repo_root / "codex-skills" / "overrides"
    manifest_outputs = {entry.output for entry in manifest.sources}
    required = REQUIRED_OVERRIDE_NAMES & manifest_outputs
    declared_outputs = set(manifest_outputs)
    canonical_manifest_path = repo_root / "codex-skills" / "manifest.yaml"
    if canonical_manifest_path.is_file() and not canonical_manifest_path.is_symlink():
        canonical_manifest = load_manifest(
            canonical_manifest_path, repo_root=repo_root
        )
        declared_outputs.update(entry.output for entry in canonical_manifest.sources)
    actual: set[str] = set()

    if override_root.exists():
        if override_root.is_symlink() or not override_root.is_dir():
            raise ValueError(f"unsafe override root: {override_root}")
        actual = {path.name for path in override_root.iterdir()}

    allowed = REQUIRED_OVERRIDE_NAMES & declared_outputs
    undeclared = actual - allowed
    if undeclared:
        raise ValueError(
            "undeclared override output(s): " + ", ".join(sorted(undeclared))
        )
    missing = required - actual
    if missing:
        raise ValueError(
            "missing required override(s): " + ", ".join(sorted(missing))
        )

    sources_by_output = {source.entry.output: source for source in sources}
    overrides: dict[str, SkillDocument] = {}
    for name in sorted(required):
        directory = override_root / name
        skill_path = directory / "SKILL.md"
        if directory.is_symlink() or not directory.is_dir():
            raise ValueError(f"unsafe override directory: {name}")
        contents = sorted(
            path.relative_to(directory).as_posix()
            for path in directory.rglob("*")
        )
        if contents != ["SKILL.md"]:
            raise ValueError(f"override {name} may contain only SKILL.md")
        if skill_path.is_symlink() or not skill_path.is_file():
            raise ValueError(f"unsafe override SKILL.md: {name}")
        try:
            with skill_path.open("r", encoding="utf-8", newline="") as override_file:
                document = _normalize_override_document(
                    parse_skill_document(override_file.read())
                )
        except (OSError, UnicodeError, ValueError) as error:
            raise ValueError(f"override {name} is malformed: {error}") from error

        source = sources_by_output[name]
        entry = source.entry
        if document.name != name or document.name != entry.output:
            raise ValueError(
                f"override skill name {document.name!r} does not match "
                f"manifest output {entry.output!r}"
            )
        expected_description = _adapt_entry_description(
            entry, source.document.description
        )
        if document.description != expected_description:
            raise ValueError(
                f"override description for {name} does not preserve source semantics"
            )
        if len(document.body.splitlines()) >= 250:
            raise ValueError(f"override {name} must be fewer than 250 lines")

        positions: list[int] = []
        for section in OVERRIDE_REQUIRED_SECTIONS:
            if document.body.count(section) != 1:
                raise ValueError(
                    f"override {name} must contain exactly one {section!r} section"
                )
            positions.append(document.body.index(section))
        if positions != sorted(positions):
            raise ValueError(f"override {name} sections are out of order")
        if "main Codex agent" not in document.body:
            raise ValueError(f"override {name} must operate in the main Codex agent")
        if "Never print, log, or expose secret values." not in document.body:
            raise ValueError(f"override {name} is missing the secret-safety clause")

        dependency_value = (
            "; ".join(entry.dependencies) if entry.dependencies else "None."
        )
        expected_dependency = f"- **Dependencies:** {dependency_value}"
        dependency_lines = [
            line
            for line in document.body.splitlines()
            if line.startswith("- **Dependencies:**")
        ]
        if dependency_lines != [expected_dependency]:
            raise ValueError(
                f"override {name} dependency contract does not match manifest"
            )
        if _MANDATORY_DELEGATION.search(document.body):
            raise ValueError(f"override {name} requires unsupported delegation")
        if ".claude/sessions" in document.body and not (
            "historical" in document.body.lower()
            and "read-only" in document.body.lower()
        ):
            raise ValueError(
                f"override {name} uses live Claude session paths instead of read-only evidence"
            )
        validate_generated_markdown(name, "SKILL.md", render_skill_document(document))
        overrides[name] = document
    return overrides


def _adapt_entry_text(
    entry: SkillEntry, text: str, *, relative_path: str = "SKILL.md"
) -> str:
    return adapt_text(
        entry.source, text, relative_path=relative_path, entry=entry
    )


def _adapt_entry_description(entry: SkillEntry, description: str) -> str:
    return adapt_description(entry.source, description, entry=entry)


def _copy_resource(
    path: Path,
    source_dir: Path,
    destination_dir: Path,
    entry: SkillEntry,
) -> None:
    relative = path.relative_to(source_dir)
    destination = destination_dir / relative
    if path.is_symlink():
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.symlink_to(os.readlink(path), target_is_directory=path.is_dir())
    elif path.is_dir():
        destination.mkdir(parents=True, exist_ok=True)
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        relative_path = relative.as_posix()
        has_resource_adapter = entry.source is not None and is_adapted_resource(
            entry.source, relative_path
        )
        if has_resource_adapter:
            with path.open("r", encoding="utf-8", newline="") as source_file:
                content = source_file.read()
            _write_text_exact(
                destination,
                _adapt_entry_text(entry, content, relative_path=relative_path),
            )
            shutil.copystat(path, destination, follow_symlinks=False)
        else:
            shutil.copy2(path, destination, follow_symlinks=False)


def _apply_directory_metadata(
    resources: tuple[Path, ...], source_dir: Path, destination_dir: Path
) -> None:
    directories = sorted(
        (path for path in resources if path.is_dir() and not path.is_symlink()),
        key=lambda path: len(path.relative_to(source_dir).parts),
        reverse=True,
    )
    for directory in directories:
        destination = destination_dir / directory.relative_to(source_dir)
        shutil.copystat(directory, destination, follow_symlinks=False)


def _validate_markdown_tree(entry: SkillEntry, destination_dir: Path) -> None:
    skill_name = entry.source or entry.output
    for path in sorted(destination_dir.rglob("*.md")):
        if not path.is_file():
            continue
        with path.open("r", encoding="utf-8", newline="") as markdown_file:
            text = markdown_file.read()
        validate_generated_markdown(
            skill_name, path.relative_to(destination_dir).as_posix(), text
        )


def _copy_generated_adapter_resources(
    repo_root: Path, entry: SkillEntry, destination_dir: Path
) -> None:
    for source_relative, destination_relative in GENERATED_ADAPTER_RESOURCES.get(
        entry.source, ()
    ):
        source_candidate = repo_root / source_relative
        if source_candidate.is_symlink():
            raise ValueError(
                f"generated adapter resource must not be a symlink: {source_relative}"
            )
        source = source_candidate.resolve(strict=True)
        if not source.is_relative_to(repo_root) or not source.is_file():
            raise ValueError(f"unsafe generated adapter resource: {source_relative}")
        destination = destination_dir / destination_relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination, follow_symlinks=False)


def _remove_generated_tree(path: Path) -> None:
    def make_owner_writable(target: Path, directory: bool) -> None:
        try:
            mode = target.lstat().st_mode
        except FileNotFoundError:
            return
        if stat.S_ISLNK(mode):
            return
        owner_permissions = stat.S_IRUSR | stat.S_IWUSR
        if directory:
            owner_permissions |= stat.S_IXUSR
        os.chmod(target, stat.S_IMODE(mode) | owner_permissions)

    make_owner_writable(path, directory=True)
    for current, directory_names, file_names in os.walk(
        path, topdown=True, followlinks=False
    ):
        current_path = Path(current)
        make_owner_writable(current_path, directory=True)
        for name in directory_names:
            make_owner_writable(current_path / name, directory=True)
        for name in file_names:
            make_owner_writable(current_path / name, directory=False)

    def retry_with_owner_permissions(function, target, error_info):
        target_path = Path(target)
        if target_path != path and not target_path.is_relative_to(path):
            raise error_info[1]
        parent = target_path.parent
        if parent == path or parent.is_relative_to(path):
            make_owner_writable(parent, directory=True)
        make_owner_writable(target_path, directory=target_path.is_dir())
        result = function(target)
        if hasattr(result, "close"):
            result.close()

    shutil.rmtree(path, onerror=retry_with_owner_permissions)


def _replace_output(staging_dir: Path, output_dir: Path) -> tuple[str, ...]:
    backup_dir: Path | None = None
    if output_dir.exists():
        backup_dir = Path(
            tempfile.mkdtemp(
                prefix=f".{output_dir.name}.backup-", dir=output_dir.parent
            )
        )
        backup_dir.rmdir()
        output_dir.rename(backup_dir)
    try:
        staging_dir.rename(output_dir)
    except BaseException:
        if backup_dir is not None:
            backup_dir.rename(output_dir)
        raise
    if backup_dir is not None:
        try:
            _remove_generated_tree(backup_dir)
        except Exception as error:
            return (
                f"new output committed; could not remove backup {backup_dir}: {error}",
            )
    return ()


def _protected_build_paths(
    repo_root: Path,
    manifest: Manifest,
    sources: list[_ValidatedSource],
) -> list[Path]:
    protected_paths = [source.source_dir for source in sources]
    protected_paths.extend(
        (
            (repo_root / ".agents-backup").resolve(strict=False),
            (repo_root / "codex-skills" / "overrides").resolve(strict=False),
            (repo_root / "codex-skills" / "promoted").resolve(strict=False),
        )
    )
    for entry in manifest.promoted:
        if entry.promoted_from is None:
            raise ValueError("promoted entry is missing provenance")
        provenance = (repo_root / entry.promoted_from).resolve(strict=False)
        if not provenance.is_relative_to(repo_root):
            raise ValueError(f"unsafe promoted provenance: {entry.promoted_from!r}")
        protected_paths.append(provenance)
    return protected_paths


def _snapshot_tree(root: Path) -> dict[str, TreeEntry]:
    snapshot: dict[str, TreeEntry] = {}
    for path in sorted(
        root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()
    ):
        relative = path.relative_to(root).as_posix()
        metadata = path.lstat()
        mode = stat.S_IMODE(metadata.st_mode)
        if stat.S_ISLNK(metadata.st_mode):
            snapshot[relative] = TreeEntry("symlink", mode, os.readlink(path))
        elif stat.S_ISDIR(metadata.st_mode):
            snapshot[relative] = TreeEntry("directory", mode)
        elif stat.S_ISREG(metadata.st_mode):
            snapshot[relative] = TreeEntry(
                "file", mode, sha256(path.read_bytes()).hexdigest()
            )
        else:
            raise ValueError(f"unsupported generated output entry: {path}")
    return snapshot


def compare_generated_trees(
    expected: dict[str, TreeEntry], actual: dict[str, TreeEntry]
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    """Return deterministic missing, extra, and changed path sets."""
    expected_paths = set(expected)
    actual_paths = set(actual)
    missing = tuple(sorted(expected_paths - actual_paths))
    extra = tuple(sorted(actual_paths - expected_paths))
    changed = tuple(
        sorted(
            path
            for path in expected_paths & actual_paths
            if expected[path] != actual[path]
        )
    )
    return missing, extra, changed


def check_collection(
    repo_root: Path, manifest: Manifest, output_dir: Path
) -> BuildCheckResult:
    """Compare canonical output with a temporary deterministic build without mutating it."""
    resolved_root = Path(repo_root).expanduser().resolve(strict=True)
    validated = _validate_sources(resolved_root, manifest)
    protected_paths = _protected_build_paths(resolved_root, manifest, validated)
    resolved_output = _validate_output_path(
        resolved_root, protected_paths, Path(output_dir)
    )
    if not resolved_output.exists():
        return BuildCheckResult(
            output_dir=resolved_output,
            errors=(f"generated output is missing: {resolved_output}",),
        )
    marker = resolved_output / GENERATED_MARKER
    if not marker.is_file() or marker.is_symlink():
        return BuildCheckResult(
            output_dir=resolved_output,
            errors=(f"generated output is not builder-owned: {resolved_output}",),
        )

    with tempfile.TemporaryDirectory(prefix="codex-skills-build-check-") as temporary:
        expected_output = Path(temporary) / "skills"
        build_collection(resolved_root, manifest, expected_output)
        expected = _snapshot_tree(expected_output)
        actual = _snapshot_tree(resolved_output)
    missing, extra, changed = compare_generated_trees(expected, actual)
    return BuildCheckResult(
        output_dir=resolved_output,
        missing_paths=missing,
        extra_paths=extra,
        changed_paths=changed,
    )


def build_collection(repo_root: Path, manifest: Manifest, output_dir: Path) -> BuildResult:
    """Build normalized Codex skills from source and promoted inputs."""
    resolved_root = Path(repo_root).expanduser().resolve(strict=True)
    validated = _validate_sources(resolved_root, manifest)
    overrides = _validate_overrides(resolved_root, manifest, validated)
    protected_paths = _protected_build_paths(resolved_root, manifest, validated)
    resolved_output = _validate_output_path(
        resolved_root,
        protected_paths,
        Path(output_dir),
    )
    promoted = _validate_promoted(resolved_root, manifest)

    resolved_output.parent.mkdir(parents=True, exist_ok=True)
    staging_dir = Path(
        tempfile.mkdtemp(
            prefix=f".{resolved_output.name}.staging-", dir=resolved_output.parent
        )
    )
    try:
        for source in validated:
            destination = staging_dir / source.entry.output
            destination.mkdir()
            for resource in source.resources:
                _copy_resource(
                    resource, source.source_dir, destination, source.entry
                )
            _copy_generated_adapter_resources(
                resolved_root, source.entry, destination
            )
            output_document = overrides.get(source.entry.output)
            if output_document is None:
                output_document = replace(
                    source.document,
                    name=source.entry.output,
                    description=_adapt_entry_description(
                        source.entry, source.document.description
                    ),
                    body=_adapt_entry_text(source.entry, source.document.body),
                )
            skill_output = destination / "SKILL.md"
            _write_text_exact(
                skill_output, render_skill_document(output_document)
            )
            if source.entry.output in overrides:
                skill_output.chmod(0o644)
            _validate_markdown_tree(source.entry, destination)
            agents_dir = destination / "agents"
            agents_dir.mkdir(parents=True, exist_ok=True)
            _write_text_exact(
                agents_dir / "openai.yaml",
                _metadata(source.entry, output_document.description),
            )
            _apply_directory_metadata(
                source.resources, source.source_dir, destination
            )
        for item in promoted:
            destination = staging_dir / item.entry.output
            destination.mkdir()
            for resource in item.resources:
                _copy_resource(
                    resource, item.source_dir, destination, item.entry
                )
            _write_text_exact(
                destination / "SKILL.md", render_skill_document(item.document)
            )
            _validate_markdown_tree(item.entry, destination)
            agents_dir = destination / "agents"
            agents_dir.mkdir(parents=True, exist_ok=True)
            _write_text_exact(
                agents_dir / "openai.yaml",
                _metadata(item.entry, item.document.description),
            )
            _apply_directory_metadata(
                item.resources, item.source_dir, destination
            )
        _write_text_exact(
            staging_dir / GENERATED_MARKER,
            "Generated by codex-skills/scripts/build.py.\n",
        )
        warnings = _replace_output(staging_dir, resolved_output)
    except BaseException as build_error:
        if staging_dir.exists():
            try:
                _remove_generated_tree(staging_dir)
            except Exception as cleanup_error:
                build_error.add_note(f"staging cleanup also failed: {cleanup_error}")
        raise

    return BuildResult(
        output_dir=resolved_output,
        built_names=tuple(
            sorted(
                [source.entry.output for source in validated]
                + [item.entry.output for item in promoted]
            )
        ),
        warnings=warnings,
    )


def main(argv: list[str] | None = None) -> int:
    default_repo = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description="Build normalized Codex skill copies.")
    parser.add_argument("--repo", type=Path, default=default_repo)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the generated output is owned and matches a deterministic build",
    )
    args = parser.parse_args(argv)

    repo_root = args.repo.expanduser().resolve(strict=True)
    output_dir = args.output or (repo_root / "codex-skills" / "skills")
    collection = load_manifest(
        repo_root / "codex-skills" / "manifest.yaml", repo_root=repo_root
    )
    if args.check:
        try:
            check_result = check_collection(repo_root, collection, output_dir)
        except (OSError, RuntimeError, ValueError, KeyError) as error:
            print(f"Build check failed: {error}", file=sys.stderr)
            return 1
        if not check_result.ok:
            for diagnostic in check_result.diagnostics:
                print(f"Build check failed: {diagnostic}", file=sys.stderr)
            return 1
        print(f"Build check passed for {check_result.output_dir}")
        return 0
    result = build_collection(repo_root, collection, output_dir)
    print(f"Built {result.count} skills in {result.output_dir}")
    for warning in result.warnings:
        print(f"Warning: {warning}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
