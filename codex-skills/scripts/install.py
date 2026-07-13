#!/usr/bin/env python3

import argparse
import ctypes
import errno
import json
import os
import re
import stat
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
TEMP_ATTEMPTS = 32
RENAME_EXCHANGE = 0x00000002
AT_FDCWD = -100


@dataclass(frozen=True)
class InstallResult:
    created: tuple[str, ...] = ()
    updated: tuple[str, ...] = ()
    unchanged: tuple[str, ...] = ()
    skipped: tuple[str, ...] = ()
    collisions: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

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
            "warnings": list(self.warnings),
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


@dataclass
class _AppliedLink:
    name: str
    operation: str
    path: Path
    new_identity: tuple[int, int, int]
    old_target: str | None = None
    old_identity: tuple[int, int, int] | None = None
    backup: Path | None = None
    recovery: Path | None = None


@dataclass(frozen=True)
class _MutationOutcome:
    errors: tuple[str, ...]
    warnings: tuple[str, ...]


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


def _temporary_path(destination: Path, name: str, kind: str) -> Path:
    return destination / f".{name}.{kind}{TEMP_MARKER}{uuid.uuid4().hex}"


def _path_identity(path: Path) -> tuple[int, int, int]:
    info = path.lstat()
    return info.st_dev, info.st_ino, stat.S_IFMT(info.st_mode)


def _create_symlink_exclusive(
    source: Path,
    destination: Path,
    name: str,
    kind: str,
    owned_paths: list[Path],
) -> Path:
    target = str(source.resolve(strict=True))
    for _ in range(TEMP_ATTEMPTS):
        candidate = _temporary_path(destination, name, kind)
        try:
            os.symlink(target, candidate, target_is_directory=True)
        except FileExistsError:
            continue
        owned_paths.append(candidate)
        return candidate
    raise FileExistsError(
        errno.EEXIST,
        f"cannot allocate exclusive {kind} link after {TEMP_ATTEMPTS} attempts",
    )


def _create_hardlink_exclusive(
    source: Path,
    destination: Path,
    name: str,
    kind: str,
    owned_paths: list[Path],
) -> Path:
    for _ in range(TEMP_ATTEMPTS):
        candidate = _temporary_path(destination, name, kind)
        try:
            os.link(source, candidate, follow_symlinks=False)
        except FileExistsError:
            continue
        owned_paths.append(candidate)
        return candidate
    raise FileExistsError(
        errno.EEXIST,
        f"cannot allocate exclusive {kind} link after {TEMP_ATTEMPTS} attempts",
    )


def _prepare_ready_link(
    source: Path,
    destination: Path,
    name: str,
    owned_paths: list[Path],
) -> Path:
    stage = _create_symlink_exclusive(
        source, destination, name, "stage", owned_paths
    )
    ready = _create_hardlink_exclusive(
        stage, destination, name, "ready", owned_paths
    )
    stage.unlink()
    return ready


def _atomic_exchange_capability_error() -> str | None:
    libc = ctypes.CDLL(None, use_errno=True)
    if sys.platform == "darwin":
        return None if hasattr(libc, "renamex_np") else "renamex_np is unavailable"
    if sys.platform.startswith("linux"):
        return None if hasattr(libc, "renameat2") else "renameat2 is unavailable"
    return f"atomic symlink exchange is unsupported on {sys.platform}"


def _atomic_exchange(first: Path, second: Path) -> None:
    capability_error = _atomic_exchange_capability_error()
    if capability_error:
        raise OSError(errno.ENOTSUP, capability_error)
    libc = ctypes.CDLL(None, use_errno=True)
    first_bytes = os.fsencode(first)
    second_bytes = os.fsencode(second)
    if sys.platform == "darwin":
        exchange = libc.renamex_np
        exchange.argtypes = (ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint)
        exchange.restype = ctypes.c_int
        result = exchange(first_bytes, second_bytes, RENAME_EXCHANGE)
    else:
        exchange = libc.renameat2
        exchange.argtypes = (
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_uint,
        )
        exchange.restype = ctypes.c_int
        result = exchange(
            AT_FDCWD,
            first_bytes,
            AT_FDCWD,
            second_bytes,
            RENAME_EXCHANGE,
        )
    if result != 0:
        error_number = ctypes.get_errno()
        raise OSError(
            error_number,
            f"atomic exchange failed for {first} and {second}: "
            f"{os.strerror(error_number)}",
        )


def _publish_without_overwrite(ready: Path, destination: Path) -> None:
    os.link(ready, destination, follow_symlinks=False)


def _cleanup_path(path: Path) -> None:
    if path.is_symlink():
        path.unlink()
    elif _lexists(path):
        raise OSError(f"refusing to clean non-symlink temporary path: {path}")


def _rollback_links(applied: list[_AppliedLink], errors: list[str]) -> None:
    for item in reversed(applied):
        try:
            if _path_identity(item.path) != item.new_identity:
                raise OSError(
                    f"installed path changed before rollback: {item.path}"
                )
            if item.operation == "created":
                if not item.path.is_symlink():
                    raise OSError(f"created path is not a symlink: {item.path}")
                item.path.unlink()
                continue

            material = item.recovery if item.recovery and _lexists(item.recovery) else item.backup
            if material is None or not _lexists(material):
                raise OSError(f"rollback material is missing for {item.name}")
            if (
                item.old_identity is None
                or _path_identity(material) != item.old_identity
                or not material.is_symlink()
                or os.readlink(material) != item.old_target
            ):
                raise OSError(f"rollback material changed for {item.name}")
            _atomic_exchange(item.path, material)
            if (
                _path_identity(item.path) != item.old_identity
                or os.readlink(item.path) != item.old_target
            ):
                raise OSError(f"atomic rollback verification failed for {item.name}")
        except (OSError, RuntimeError) as rollback_error:
            errors.append(f"rollback failed for {item.name}: {rollback_error}")


def _apply_plan(source: _Source, destination: Path, plan: _Plan) -> _MutationOutcome:
    created_directories: list[Path] = []
    owned_paths: list[Path] = []
    recovery_paths: list[Path] = []
    applied: list[_AppliedLink] = []
    previous = dict(plan.previous_links)
    errors: list[str] = []
    warnings: list[str] = []
    committed = False
    try:
        _create_destination(destination, created_directories)
        if destination.is_symlink() or not destination.is_dir():
            raise OSError(f"destination became unsafe: {destination}")
        for name in sorted((*plan.created, *plan.updated)):
            path = destination / name
            operation = "created" if name in plan.created else "updated"
            old_target = previous.get(name)
            if operation == "created":
                if _lexists(path):
                    raise OSError(f"destination changed during install: {path}")
                ready = _prepare_ready_link(
                    source.root / name, destination, name, owned_paths
                )
                new_identity = _path_identity(ready)
                try:
                    _publish_without_overwrite(ready, path)
                except (OSError, RuntimeError):
                    if (
                        path.is_symlink()
                        and _path_identity(path) == new_identity
                    ):
                        applied.append(
                            _AppliedLink(name, operation, path, new_identity)
                        )
                    raise
                applied.append(
                    _AppliedLink(name, operation, path, new_identity)
                )
                ready.unlink()
                continue

            if not path.is_symlink() or os.readlink(path) != old_target:
                raise OSError(f"managed link changed during install: {path}")
            old_identity = _path_identity(path)
            backup = _create_hardlink_exclusive(
                path, destination, name, "backup", owned_paths
            )
            if _path_identity(backup) != old_identity:
                raise OSError(f"managed link changed while backing up: {path}")
            ready = _prepare_ready_link(
                source.root / name, destination, name, owned_paths
            )
            new_identity = _path_identity(ready)
            item = _AppliedLink(
                name,
                operation,
                path,
                new_identity,
                old_target=old_target,
                old_identity=old_identity,
                backup=backup,
            )
            try:
                _atomic_exchange(path, ready)
            except (OSError, RuntimeError):
                if (
                    path.is_symlink()
                    and ready.is_symlink()
                    and _path_identity(path) == new_identity
                    and _path_identity(ready) == old_identity
                    and os.readlink(ready) == old_target
                ):
                    applied.append(item)
                raise
            if (
                _path_identity(ready) != old_identity
                or not ready.is_symlink()
                or os.readlink(ready) != old_target
            ):
                _atomic_exchange(path, ready)
                raise OSError(f"managed link changed during atomic exchange: {path}")
            applied.append(item)
            ready.unlink()

        updates = [item for item in applied if item.operation == "updated"]
        for item in updates:
            assert item.backup is not None
            item.recovery = _create_hardlink_exclusive(
                item.backup,
                destination,
                item.name,
                "recovery",
                recovery_paths,
            )
        for item in updates:
            assert item.backup is not None
            item.backup.unlink()
        committed = True
    except (OSError, RuntimeError) as error:
        errors.append(f"installation mutation failed: {error}")
        _rollback_links(applied, errors)
    finally:
        if committed:
            for recovery in recovery_paths:
                try:
                    _cleanup_path(recovery)
                except (OSError, RuntimeError) as cleanup_error:
                    warnings.append(
                        f"committed install left recovery link {recovery}: {cleanup_error}"
                    )
        else:
            for path in reversed((*owned_paths, *recovery_paths)):
                try:
                    _cleanup_path(path)
                except (OSError, RuntimeError) as cleanup_error:
                    errors.append(f"temporary cleanup failed for {path}: {cleanup_error}")
            for directory in reversed(created_directories):
                try:
                    directory.rmdir()
                except OSError:
                    pass
    return _MutationOutcome(tuple(errors), tuple(warnings))


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
    if plan.updated:
        capability_error = _atomic_exchange_capability_error()
        if capability_error:
            return plan.result(
                errors=(f"atomic exchange unsupported: {capability_error}",)
            )
    outcome = _apply_plan(source, target, plan)
    if outcome.errors:
        return InstallResult(
            unchanged=plan.unchanged,
            skipped=plan.skipped,
            collisions=plan.collisions,
            errors=outcome.errors,
            warnings=outcome.warnings,
        )
    return InstallResult(
        created=plan.created,
        updated=plan.updated,
        unchanged=plan.unchanged,
        skipped=plan.skipped,
        collisions=plan.collisions,
        warnings=outcome.warnings,
    )


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
        for warning in result.warnings:
            print(f"Warning: {warning}", file=sys.stderr)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
