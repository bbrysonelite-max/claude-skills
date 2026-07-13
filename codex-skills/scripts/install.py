#!/usr/bin/env python3

import argparse
import json
import os
import re
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path

try:
    from scripts.common import SAFE_SKILL_NAME
    from scripts.validate import (
        EXPECTED_SKILL_COUNT,
        validate_approved_existing,
        validate_collection,
    )
except ModuleNotFoundError:  # Support direct execution as scripts/install.py.
    from common import SAFE_SKILL_NAME  # type: ignore[no-redef]
    from validate import (  # type: ignore[no-redef]
        EXPECTED_SKILL_COUNT,
        validate_approved_existing,
        validate_collection,
    )


VALIDATION_FINGERPRINT = re.compile(
    r"(?m)^- \*\*Structural fingerprint:\*\* `([0-9a-f]{64})`$"
)
GENERATED_MARKER = ".codex-skills-generated"
TEMP_MARKER = ".codex-install-"


@dataclass(frozen=True)
class InstallResult:
    created: tuple[str, ...] = ()
    updated: tuple[str, ...] = ()
    unchanged: tuple[str, ...] = ()
    skipped: tuple[str, ...] = ()
    collisions: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return not self.collisions and not self.errors

    def to_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "created": list(self.created),
            "updated": list(self.updated),
            "unchanged": list(self.unchanged),
            "skipped": list(self.skipped),
            "collisions": list(self.collisions),
            "errors": list(self.errors),
        }


@dataclass(frozen=True)
class _Source:
    root: Path
    repository: Path
    names: tuple[str, ...]


@dataclass(frozen=True)
class _Plan:
    created: tuple[str, ...]
    updated: tuple[str, ...]
    unchanged: tuple[str, ...]
    skipped: tuple[str, ...]
    collisions: tuple[str, ...]
    errors: tuple[str, ...]
    previous_links: tuple[tuple[str, str], ...]

    def result(self, *, errors: tuple[str, ...] | None = None) -> InstallResult:
        return InstallResult(
            created=self.created,
            updated=self.updated,
            unchanged=self.unchanged,
            skipped=self.skipped,
            collisions=self.collisions,
            errors=self.errors if errors is None else errors,
        )


def _lexists(path: Path) -> bool:
    return os.path.lexists(path)


def _overlaps(first: Path, second: Path) -> bool:
    return first == second or first.is_relative_to(second) or second.is_relative_to(first)


def _source_preflight(collection: Path) -> _Source:
    requested = Path(collection).expanduser()
    if requested.is_symlink() or not requested.is_dir():
        raise ValueError(f"source collection is missing or unsafe: {requested}")
    source = requested.resolve(strict=True)
    repository = source.parent.parent
    canonical = repository / "codex-skills" / "skills"
    if source != canonical or source.name != "skills":
        raise ValueError(
            "source collection must be the canonical codex-skills/skills directory"
        )
    marker = source / GENERATED_MARKER
    if marker.is_symlink() or not marker.is_file():
        raise ValueError(f"source collection is not builder-owned: {source}")

    report = validate_collection(
        repository,
        collect_evidence=False,
        structural_only=True,
    )
    validation_path = source.parent / "VALIDATION.md"
    try:
        validation_text = validation_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise ValueError(f"source validation report cannot be read: {error}") from error
    match = VALIDATION_FINGERPRINT.search(validation_text)
    validation_errors: list[str] = []
    if match is None or match.group(1) != report.structural_fingerprint:
        validation_errors.append(
            f"source validation report is stale for collection: {validation_path}"
        )
    if not report.ok:
        detail = "; ".join(report.errors)
        validation_errors.append(
            f"source collection failed structural validation: {detail}"
        )
    if validation_errors:
        raise ValueError("; ".join(validation_errors))
    names = tuple(sorted(result.name for result in report.skill_results))
    if len(names) != EXPECTED_SKILL_COUNT:
        raise ValueError(
            f"source collection must contain exactly {EXPECTED_SKILL_COUNT} skills, "
            f"found {len(names)}"
        )
    return _Source(source, repository, names)


def _symlink_ancestor_error(path: Path) -> str | None:
    absolute = path if path.is_absolute() else Path.cwd() / path
    current = Path(absolute.anchor)
    user_controlled = False
    for part in absolute.parts[1:-1]:
        current /= part
        if not _lexists(current):
            continue
        try:
            info = current.lstat()
        except OSError as error:
            return f"destination ancestor cannot be inspected: {current}: {error}"
        if current.is_symlink():
            if user_controlled:
                return f"destination has a symlinked ancestor: {current}"
            continue
        if info.st_uid == os.getuid() and current != Path(absolute.anchor):
            user_controlled = True
    return None


def _destination_preflight(destination: Path, source: _Source) -> Path:
    target = Path(destination).expanduser()
    if not target.is_absolute():
        target = Path.cwd() / target
    if target.is_symlink():
        raise ValueError(f"destination must not be a symlink: {target}")
    if _lexists(target) and not target.is_dir():
        raise ValueError(f"destination must be a directory: {target}")
    ancestor_error = _symlink_ancestor_error(target)
    if ancestor_error:
        raise ValueError(ancestor_error)

    resolved = target.resolve(strict=False)
    if _overlaps(resolved, source.root):
        raise ValueError(f"destination overlaps source collection: {target}")
    if _overlaps(resolved, source.repository):
        raise ValueError(f"destination overlaps source repository: {target}")
    return target


def _managed_link_target(path: Path, source_root: Path) -> tuple[Path, str] | None:
    try:
        raw_target = os.readlink(path)
    except OSError:
        return None
    candidate = Path(raw_target)
    if not candidate.is_absolute():
        candidate = path.parent / candidate
    target = candidate.resolve(strict=False)
    if target.parent != source_root:
        return None
    return target, raw_target


def _plan_install(
    source: _Source,
    destination: Path,
    skip_existing: tuple[str, ...],
) -> _Plan:
    created: list[str] = []
    updated: list[str] = []
    unchanged: list[str] = []
    skipped: list[str] = []
    collisions: list[str] = []
    errors: list[str] = []
    previous_links: list[tuple[str, str]] = []

    requested_skips = set(skip_existing)
    invalid_skips = sorted(
        name
        for name in requested_skips
        if SAFE_SKILL_NAME.fullmatch(name) is None or name not in source.names
    )
    if invalid_skips:
        errors.append("unknown skip-existing skill(s): " + ", ".join(invalid_skips))

    for name in source.names:
        path = destination / name
        exists = _lexists(path)
        if name in requested_skips:
            if not exists:
                errors.append(f"skip-existing skill {name} does not exist")
                continue
            if path.is_symlink() and _managed_link_target(path, source.root) is not None:
                errors.append(f"skip-existing skill {name} is already a managed link")
                continue
            validation_errors = validate_approved_existing(path, name)
            if validation_errors:
                errors.extend(
                    f"skip-existing skill {name}: {error}"
                    for error in validation_errors
                )
            else:
                skipped.append(name)
            continue

        if not exists:
            created.append(name)
            continue
        if not path.is_symlink():
            collisions.append(name)
            continue
        managed = _managed_link_target(path, source.root)
        if managed is None:
            collisions.append(name)
            continue
        target, raw_target = managed
        if target == source.root / name and target.is_dir():
            unchanged.append(name)
        else:
            updated.append(name)
            previous_links.append((name, raw_target))

    return _Plan(
        tuple(created),
        tuple(updated),
        tuple(unchanged),
        tuple(skipped),
        tuple(collisions),
        tuple(errors),
        tuple(previous_links),
    )


def _create_destination(destination: Path, created: list[Path]) -> None:
    missing: list[Path] = []
    current = destination
    while not _lexists(current):
        missing.append(current)
        if current.parent == current:
            break
        current = current.parent
    if current.is_symlink() or not current.is_dir():
        raise OSError(f"destination parent is unsafe: {current}")

    for path in reversed(missing):
        path.mkdir()
        created.append(path)
        if path.is_symlink() or not path.is_dir():
            raise OSError(f"destination directory became unsafe: {path}")


def _temporary_link(destination: Path, name: str) -> Path:
    return destination / f".{name}{TEMP_MARKER}{uuid.uuid4().hex}"


def _remove_link(path: Path) -> None:
    if path.is_symlink():
        path.unlink()


def _stage_link(
    source: Path,
    destination: Path,
    name: str,
    temporary_paths: list[Path],
) -> Path:
    temporary = _temporary_link(destination, name)
    ready = _temporary_link(destination, f"{name}.ready")
    temporary_paths.extend((temporary, ready))
    os.symlink(
        str(source.resolve(strict=True)),
        temporary,
        target_is_directory=True,
    )
    os.replace(temporary, ready)
    return ready


def _publish_without_overwrite(ready: Path, destination: Path) -> None:
    os.link(ready, destination, follow_symlinks=False)


def _restore_unexpected_path(backup: Path, destination: Path) -> None:
    if _lexists(destination):
        raise OSError(f"cannot restore concurrent path without overwrite: {destination}")
    if backup.is_dir() and not backup.is_symlink():
        backup.rename(destination)
        return
    os.link(backup, destination, follow_symlinks=False)
    backup.unlink()


def _restore_link(
    path: Path,
    backup: Path,
    raw_target: str,
    temporary_paths: list[Path],
) -> None:
    if _lexists(path):
        if not path.is_symlink():
            raise OSError(f"cannot restore managed link over real path: {path}")
        path.unlink()
    try:
        os.replace(backup, path)
    except OSError:
        if _lexists(path):
            raise
        replacement = _temporary_link(path.parent, path.name)
        temporary_paths.append(replacement)
        os.symlink(raw_target, replacement, target_is_directory=True)
        _publish_without_overwrite(replacement, path)
        replacement.unlink()


def _apply_plan(source: _Source, destination: Path, plan: _Plan) -> tuple[str, ...]:
    created_directories: list[Path] = []
    temporary_paths: list[Path] = []
    applied: list[tuple[str, str, str | None, Path | None]] = []
    previous = dict(plan.previous_links)
    errors: list[str] = []
    try:
        _create_destination(destination, created_directories)
        if destination.is_symlink() or not destination.is_dir():
            raise OSError(f"destination became unsafe: {destination}")
        for name in sorted((*plan.created, *plan.updated)):
            path = destination / name
            operation = "created" if name in plan.created else "updated"
            old_target = previous.get(name)
            if operation == "created" and _lexists(path):
                raise OSError(f"destination changed during install: {path}")
            if operation == "updated":
                if not path.is_symlink() or os.readlink(path) != old_target:
                    raise OSError(f"managed link changed during install: {path}")
                backup = _temporary_link(destination, f"{name}.backup")
                temporary_paths.append(backup)
                os.replace(path, backup)
                if not backup.is_symlink() or os.readlink(backup) != old_target:
                    _restore_unexpected_path(backup, path)
                    raise OSError(f"managed link changed during install: {path}")
                applied.append((name, operation, old_target, backup))
            else:
                backup = None

            ready = _stage_link(source.root / name, destination, name, temporary_paths)
            _publish_without_overwrite(ready, path)
            if operation == "created":
                applied.append((name, operation, old_target, backup))
            ready.unlink()
    except (OSError, RuntimeError) as error:
        errors.append(f"installation mutation failed: {error}")
        for name, operation, old_target, backup in reversed(applied):
            path = destination / name
            try:
                if operation == "created":
                    if not path.is_symlink():
                        raise OSError(f"created path is no longer a symlink: {path}")
                    path.unlink()
                elif old_target is not None and backup is not None:
                    _restore_link(path, backup, old_target, temporary_paths)
            except OSError as rollback_error:
                errors.append(f"rollback failed for {name}: {rollback_error}")
    finally:
        for temporary in temporary_paths:
            try:
                _remove_link(temporary)
            except OSError as cleanup_error:
                errors.append(f"temporary cleanup failed for {temporary}: {cleanup_error}")
        if errors:
            for directory in reversed(created_directories):
                try:
                    directory.rmdir()
                except OSError:
                    pass
    return tuple(errors)


def install(
    collection: Path | None = None,
    destination: Path | None = None,
    *,
    skip_existing: tuple[str, ...] = (),
    dry_run: bool = False,
) -> InstallResult:
    """Plan and transactionally install a validated generated skill collection."""
    if collection is None:
        collection = Path(__file__).resolve().parents[1] / "skills"
    if destination is None:
        codex_home = Path(os.environ.get("CODEX_HOME") or "~/.codex").expanduser()
        destination = codex_home / "skills"

    try:
        source = _source_preflight(Path(collection))
        target = _destination_preflight(Path(destination), source)
        plan = _plan_install(source, target, tuple(skip_existing))
    except (OSError, UnicodeError, ValueError, RuntimeError) as error:
        return InstallResult(errors=(str(error),))

    if plan.errors or plan.collisions or dry_run:
        return plan.result()
    mutation_errors = _apply_plan(source, target, plan)
    if mutation_errors:
        return InstallResult(
            unchanged=plan.unchanged,
            skipped=plan.skipped,
            collisions=plan.collisions,
            errors=mutation_errors,
        )
    return plan.result()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Install generated Codex skills.")
    parser.add_argument("--source", type=Path)
    parser.add_argument("--dest", type=Path)
    parser.add_argument("--skip-existing", action="append", default=[])
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    result = install(
        args.source,
        args.dest,
        skip_existing=tuple(args.skip_existing),
        dry_run=args.dry_run,
    )
    if args.json:
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    else:
        print(
            f"Created {len(result.created)}, updated {len(result.updated)}, "
            f"unchanged {len(result.unchanged)}, skipped {len(result.skipped)}."
        )
        for name in result.collisions:
            print(f"Collision: {name}", file=sys.stderr)
        for error in result.errors:
            print(f"Error: {error}", file=sys.stderr)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
