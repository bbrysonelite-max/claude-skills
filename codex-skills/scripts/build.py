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
    "cache",
    "logs",
    "runtime",
}
EXCLUDED_FILENAMES = {".DS_Store"}
GENERATED_MARKER = ".codex-skills-generated"


@dataclass(frozen=True)
class BuildResult:
    output_dir: Path
    built_names: tuple[str, ...]
    warnings: tuple[str, ...] = ()

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
    if resolved_output.is_dir() and not is_canonical:
        contents = list(resolved_output.iterdir())
        marker = resolved_output / GENERATED_MARKER
        is_owned = marker.is_file() and not marker.is_symlink()
        if contents and not is_owned:
            raise ValueError(f"external output is not builder-owned: {output_dir}")
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


def _copy_resource(path: Path, source_dir: Path, destination_dir: Path) -> None:
    relative = path.relative_to(source_dir)
    destination = destination_dir / relative
    if path.is_symlink():
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.symlink_to(os.readlink(path), target_is_directory=path.is_dir())
    elif path.is_dir():
        destination.mkdir(parents=True, exist_ok=True)
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
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


def build_collection(repo_root: Path, manifest: Manifest, output_dir: Path) -> BuildResult:
    """Build normalized copies for source entries; promoted entries are handled later."""
    resolved_root = Path(repo_root).expanduser().resolve(strict=True)
    validated = _validate_sources(resolved_root, manifest)
    protected_paths = [source.source_dir for source in validated]
    protected_paths.append((resolved_root / ".agents-backup").resolve(strict=False))
    for entry in manifest.promoted:
        if entry.promoted_from is None:
            raise ValueError("promoted entry is missing provenance")
        provenance = (resolved_root / entry.promoted_from).resolve(strict=False)
        if not provenance.is_relative_to(resolved_root):
            raise ValueError(f"unsafe promoted provenance: {entry.promoted_from!r}")
        protected_paths.append(provenance)
    resolved_output = _validate_output_path(
        resolved_root,
        protected_paths,
        Path(output_dir),
    )

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
            output_document = replace(source.document, name=source.entry.output)
            _write_text_exact(
                destination / "SKILL.md", render_skill_document(output_document)
            )
            for resource in source.resources:
                _copy_resource(resource, source.source_dir, destination)
            agents_dir = destination / "agents"
            agents_dir.mkdir(parents=True, exist_ok=True)
            _write_text_exact(
                agents_dir / "openai.yaml",
                _metadata(source.entry, source.document.description),
            )
            _apply_directory_metadata(
                source.resources, source.source_dir, destination
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
        built_names=tuple(source.entry.output for source in validated),
        warnings=warnings,
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
    for warning in result.warnings:
        print(f"Warning: {warning}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
