import json
import re
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path, PurePosixPath


EXCLUDED_SOURCE_DIRECTORIES = {"codex-skills", "docs"}
ALLOWED_CONVERSIONS = {"native", "adapted", "dependency-required"}
MANIFEST_KEYS = {"sources", "promoted"}
ENTRY_KEYS = {
    "source",
    "promoted_from",
    "output",
    "conversion",
    "dependencies",
    "notes",
}
SAFE_SKILL_NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")


@dataclass(frozen=True)
class SkillEntry:
    source: str | None
    promoted_from: str | None
    output: str
    conversion: str
    dependencies: tuple[str, ...]
    notes: str


@dataclass(frozen=True)
class Manifest:
    sources: tuple[SkillEntry, ...]
    promoted: tuple[SkillEntry, ...]

    @property
    def entries(self) -> tuple[SkillEntry, ...]:
        return self.sources + self.promoted


def _require_exact_keys(data: dict, expected: set[str], context: str) -> None:
    unknown = set(data) - expected
    missing = expected - set(data)
    if unknown:
        raise ValueError(f"unknown {context} keys: {sorted(unknown)}")
    if missing:
        raise ValueError(f"missing {context} keys: {sorted(missing)}")


def _parse_entry(raw: object, section: str, index: int) -> SkillEntry:
    if not isinstance(raw, dict):
        raise ValueError(f"{section}[{index}] must be an object")
    _require_exact_keys(raw, ENTRY_KEYS, "entry")

    source = raw["source"]
    promoted_from = raw["promoted_from"]
    output = raw["output"]
    conversion = raw["conversion"]
    dependencies = raw["dependencies"]
    notes = raw["notes"]

    if section == "sources":
        if not isinstance(source, str) or not source:
            raise ValueError("source entry must set source to a non-empty string")
        if promoted_from is not None:
            raise ValueError("source entry must not set promoted_from")
    else:
        if source is not None:
            raise ValueError("promoted entry must not set source")
        if not isinstance(promoted_from, str) or not promoted_from:
            raise ValueError("promoted entry must set promoted_from to a non-empty string")
        provenance_path = PurePosixPath(promoted_from)
        if (
            provenance_path.is_absolute()
            or ".." in provenance_path.parts
            or "\\" in promoted_from
        ):
            raise ValueError(f"unsafe promoted provenance: {promoted_from!r}")

    if source is not None and SAFE_SKILL_NAME.fullmatch(source) is None:
        raise ValueError(f"unsafe source name: {source!r}")
    if not isinstance(output, str) or SAFE_SKILL_NAME.fullmatch(output) is None:
        raise ValueError(f"unsafe output name: {output!r}")
    if not isinstance(conversion, str) or conversion not in ALLOWED_CONVERSIONS:
        raise ValueError(f"invalid conversion: {conversion!r}")
    if not isinstance(dependencies, list):
        raise ValueError("dependencies must be a list")
    if not all(isinstance(dependency, str) and dependency.strip() for dependency in dependencies):
        raise ValueError("dependencies must contain non-empty strings")
    requires_dependencies = conversion == "dependency-required"
    if requires_dependencies != bool(dependencies):
        raise ValueError("conversion and dependencies are inconsistent")
    if not isinstance(notes, str) or not notes.strip():
        raise ValueError("notes must be a non-empty string")

    return SkillEntry(
        source=source,
        promoted_from=promoted_from,
        output=output,
        conversion=conversion,
        dependencies=tuple(dependencies),
        notes=notes,
    )


def load_manifest(path: Path, repo_root: Path | None = None) -> Manifest:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("manifest must be an object")
    _require_exact_keys(data, MANIFEST_KEYS, "top-level")
    if not isinstance(data["sources"], list) or not isinstance(data["promoted"], list):
        raise ValueError("manifest sources and promoted values must be lists")

    sources = tuple(
        _parse_entry(raw, "sources", index) for index, raw in enumerate(data["sources"])
    )
    promoted = tuple(
        _parse_entry(raw, "promoted", index) for index, raw in enumerate(data["promoted"])
    )

    source_names = [entry.source for entry in sources]
    if len(source_names) != len(set(source_names)):
        raise ValueError("duplicate source name")
    outputs = [entry.output for entry in sources + promoted]
    if len(outputs) != len(set(outputs)):
        raise ValueError("duplicate output name")

    if repo_root is not None:
        resolved_root = Path(repo_root).resolve(strict=True)
        for entry in sources:
            candidate = resolved_root / entry.source
            try:
                resolved_candidate = candidate.resolve(strict=True)
            except FileNotFoundError:
                raise ValueError(f"source path does not exist: {entry.source}")
            if not resolved_candidate.is_relative_to(resolved_root):
                raise ValueError(f"source path escapes repo root: {entry.source}")
            if not resolved_candidate.is_dir():
                raise ValueError(f"source path is not a directory: {entry.source}")
        for entry in promoted:
            candidate = resolved_root / entry.promoted_from
            try:
                resolved_candidate = candidate.resolve(strict=True)
            except FileNotFoundError:
                raise ValueError(
                    f"promoted provenance does not exist: {entry.promoted_from}"
                )
            if not resolved_candidate.is_relative_to(resolved_root):
                raise ValueError(
                    f"promoted provenance escapes repo root: {entry.promoted_from}"
                )
            if not resolved_candidate.is_file():
                raise ValueError(
                    f"promoted provenance is not a file: {entry.promoted_from}"
                )

    return Manifest(sources=sources, promoted=promoted)


def discover_source_skills(root: Path) -> list[Path]:
    return sorted(
        (
            child
            for child in root.iterdir()
            if child.is_dir()
            and not child.name.startswith(".")
            and child.name not in EXCLUDED_SOURCE_DIRECTORIES
            and (child / "SKILL.md").is_file()
        ),
        key=lambda path: path.name,
    )


def hash_protected_sources(root: Path) -> dict[str, str]:
    protected_roots = [*discover_source_skills(root), root / ".agents-backup"]
    protected_files = sorted(
        (
            path
            for protected_root in protected_roots
            for path in protected_root.rglob("*")
            if path.is_file()
        ),
        key=lambda path: path.relative_to(root).as_posix(),
    )

    return {
        path.relative_to(root).as_posix(): sha256(path.read_bytes()).hexdigest()
        for path in protected_files
    }
