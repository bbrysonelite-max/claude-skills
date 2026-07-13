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
FRONTMATTER_KEY = re.compile(r"[A-Za-z0-9_-]+\Z")


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


@dataclass(frozen=True)
class SkillDocument:
    name: str
    description: str
    body: str


def _parse_quoted_scalar(value: str, field: str) -> str:
    if value.startswith('"'):
        try:
            parsed = json.loads(value)
        except (json.JSONDecodeError, TypeError) as error:
            raise ValueError(f"malformed {field} scalar") from error
        if not isinstance(parsed, str):
            raise ValueError(f"{field} must be a string")
        return parsed
    if value.startswith("'"):
        parsed_characters: list[str] = []
        index = 1
        while index < len(value):
            character = value[index]
            if character != "'":
                parsed_characters.append(character)
                index += 1
                continue
            if index + 1 < len(value) and value[index + 1] == "'":
                parsed_characters.append("'")
                index += 2
                continue
            if index != len(value) - 1:
                raise ValueError(f"malformed {field} scalar")
            return "".join(parsed_characters)
        raise ValueError(f"malformed {field} scalar")
    return value.strip()


def _parse_block_scalar(lines: list[str], style: str) -> str:
    if not lines:
        return ""
    nonempty = [line for line in lines if line.strip()]
    if any(line.startswith("\t") for line in nonempty):
        raise ValueError("block scalar indentation must use spaces")
    indent = min((len(line) - len(line.lstrip(" ")) for line in nonempty), default=0)
    if nonempty and indent == 0:
        raise ValueError("block scalar contents must be indented")
    content = [line[indent:] if line.strip() else "" for line in lines]
    if style == "|":
        while content and not content[-1]:
            content.pop()
        return "\n".join(content) + ("\n" if content else "")

    paragraphs: list[str] = []
    current: list[str] = []
    blank_count = 0
    for line in content:
        if line:
            if blank_count and current:
                paragraphs.append(" ".join(current))
                paragraphs.extend("" for _ in range(blank_count - 1))
                current = []
            blank_count = 0
            current.append(line)
        else:
            blank_count += 1
    if current:
        paragraphs.append(" ".join(current))
    return "\n\n".join(paragraphs) + "\n"


def parse_skill_document(text: str) -> SkillDocument:
    """Parse the required source frontmatter and retain the body byte-for-byte."""
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].rstrip("\r\n") != "---":
        raise ValueError("SKILL.md is missing the opening frontmatter delimiter")

    closing_index = next(
        (
            index
            for index, line in enumerate(lines[1:], start=1)
            if line.rstrip("\r\n") == "---"
        ),
        None,
    )
    if closing_index is None:
        raise ValueError("SKILL.md is missing the closing frontmatter delimiter")

    frontmatter = [line.rstrip("\r\n") for line in lines[1:closing_index]]
    values: dict[str, str] = {}
    index = 0
    while index < len(frontmatter):
        line = frontmatter[index]
        if not line.strip() or line.lstrip().startswith("#"):
            index += 1
            continue
        if line[:1].isspace() or ":" not in line:
            raise ValueError(f"malformed frontmatter line: {line!r}")
        key, raw_value = line.split(":", 1)
        if FRONTMATTER_KEY.fullmatch(key) is None:
            raise ValueError(f"malformed frontmatter key: {key!r}")
        if key in values:
            raise ValueError(f"duplicate frontmatter field: {key}")
        value = raw_value.strip()
        if key not in {"name", "description"}:
            index += 1
            if not value or re.fullmatch(r"[>|]", value):
                while index < len(frontmatter):
                    candidate = frontmatter[index]
                    if candidate and not candidate[:1].isspace():
                        break
                    index += 1
            continue
        if re.fullmatch(r"[>|]", value):
            block_lines: list[str] = []
            index += 1
            while index < len(frontmatter):
                candidate = frontmatter[index]
                if candidate and not candidate[:1].isspace():
                    break
                block_lines.append(candidate)
                index += 1
            values[key] = _parse_block_scalar(block_lines, value)
            continue
        values[key] = _parse_quoted_scalar(value, key)
        index += 1

    name = values.get("name")
    description = values.get("description")
    if not name:
        raise ValueError("SKILL.md frontmatter requires a non-empty name")
    if SAFE_SKILL_NAME.fullmatch(name) is None:
        raise ValueError(f"unsafe skill name: {name!r}")
    if description is None or not description.strip():
        raise ValueError("SKILL.md frontmatter requires a non-empty description")
    return SkillDocument(
        name=name,
        description=description,
        body="".join(lines[closing_index + 1 :]),
    )


def render_skill_document(document: SkillDocument) -> str:
    """Render normalized Codex frontmatter while preserving the source body."""
    name = json.dumps(document.name, ensure_ascii=True)
    description = json.dumps(document.description.rstrip("\n"), ensure_ascii=True)
    return f"---\nname: {name}\ndescription: {description}\n---\n{document.body}"


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
