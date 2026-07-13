#!/usr/bin/env python3

import argparse
import json
import os
import re
import shutil
from dataclasses import dataclass, replace
from pathlib import Path

try:
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
    "logs",
}
EXCLUDED_FILENAMES = {".DS_Store"}


@dataclass(frozen=True)
class BuildResult:
    output_dir: Path
    built_names: tuple[str, ...]

    @property
    def count(self) -> int:
        return len(self.built_names)


@dataclass(frozen=True)
class _ValidatedSource:
    entry: SkillEntry
    source_dir: Path
    document: SkillDocument
    resources: tuple[Path, ...]


def _is_relative_to(path: Path, parent: Path) -> bool:
    return path == parent or path.is_relative_to(parent)


def _validate_output_path(repo_root: Path, sources: list[Path], output_dir: Path) -> Path:
    resolved_output = output_dir.expanduser().resolve(strict=False)
    if output_dir.is_symlink():
        raise ValueError(f"unsafe output path is a symlink: {output_dir}")
    if resolved_output == repo_root or repo_root.is_relative_to(resolved_output):
        raise ValueError(f"unsafe output path overlaps repository root: {output_dir}")
    for source in sources:
        if _is_relative_to(resolved_output, source) or _is_relative_to(source, resolved_output):
            raise ValueError(f"unsafe output path overlaps source skill: {output_dir}")
    if resolved_output.exists() and not resolved_output.is_dir():
        raise ValueError(f"unsafe output path is not a directory: {output_dir}")
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
    return tuple(sorted(resources, key=lambda path: path.relative_to(source_dir).as_posix()))


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


def _copy_resource(path: Path, source_dir: Path, destination_dir: Path) -> None:
    relative = path.relative_to(source_dir)
    destination = destination_dir / relative
    if path.is_symlink():
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.symlink_to(os.readlink(path), target_is_directory=path.is_dir())
    elif path.is_dir():
        destination.mkdir(parents=True, exist_ok=True)
        shutil.copystat(path, destination, follow_symlinks=False)
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination, follow_symlinks=False)


def build_collection(repo_root: Path, manifest: Manifest, output_dir: Path) -> BuildResult:
    """Build normalized copies for source entries; promoted entries are handled later."""
    resolved_root = Path(repo_root).expanduser().resolve(strict=True)
    validated = _validate_sources(resolved_root, manifest)
    resolved_output = _validate_output_path(
        resolved_root,
        [source.source_dir for source in validated],
        Path(output_dir),
    )

    if resolved_output.exists():
        shutil.rmtree(resolved_output)
    resolved_output.mkdir(parents=True)

    for source in validated:
        destination = resolved_output / source.entry.output
        destination.mkdir()
        output_document = replace(source.document, name=source.entry.output)
        (destination / "SKILL.md").write_text(
            render_skill_document(output_document), encoding="utf-8"
        )
        for resource in source.resources:
            _copy_resource(resource, source.source_dir, destination)
        agents_dir = destination / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        (agents_dir / "openai.yaml").write_text(
            _metadata(source.entry, source.document.description), encoding="utf-8"
        )

    return BuildResult(
        output_dir=resolved_output,
        built_names=tuple(source.entry.output for source in validated),
    )


def main(argv: list[str] | None = None) -> int:
    default_repo = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description="Build normalized Codex skill copies.")
    parser.add_argument("--repo", type=Path, default=default_repo)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)

    repo_root = args.repo.expanduser().resolve(strict=True)
    output_dir = args.output or (repo_root / "codex-skills" / "skills")
    collection = load_manifest(
        repo_root / "codex-skills" / "manifest.yaml", repo_root=repo_root
    )
    result = build_collection(repo_root, collection, output_dir)
    print(f"Built {result.count} skills in {result.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
