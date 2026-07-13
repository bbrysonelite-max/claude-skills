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
    planned_created: tuple[str, ...] = ()
    planned_updated: tuple[str, ...] = ()
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
            "planned_created": list(self.planned_created),
            "planned_updated": list(self.planned_updated),
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
            planned_created=self.created,
            planned_updated=self.updated,
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
    displaced: Path | None = None
    displaced_identity: tuple[int, int, int] | None = None


@dataclass(frozen=True)
class _OwnedPath:
    path: Path
    identity: tuple[int, int, int]
    target: str | None = None


@dataclass(frozen=True)
class _MutationOutcome:
    errors: tuple[str, ...]
    warnings: tuple[str, ...]


class _ManualRecoveryError(OSError):
    def __init__(
        self,
        message: str,
        material: Path,
        material_identity: tuple[int, int, int],
    ) -> None:
        super().__init__(message)
        self.material = material
        self.material_identity = material_identity


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


def _allowed_system_alias(path: Path) -> bool:
    if sys.platform != "darwin":
        return False
    expected = {
        Path("/tmp"): Path("/private/tmp"),
        Path("/var"): Path("/private/var"),
    }.get(path)
    if expected is None:
        return False
    try:
        raw_target = Path(os.readlink(path))
    except OSError:
        return False
    lexical_target = raw_target if raw_target.is_absolute() else path.parent / raw_target
    return Path(os.path.normpath(lexical_target)) == expected


def _symlink_ancestor_error(path: Path) -> str | None:
    absolute = path if path.is_absolute() else Path.cwd() / path
    current = Path(absolute.anchor)
    for part in absolute.parts[1:-1]:
        current /= part
        if not _lexists(current):
            continue
        try:
            info = current.lstat()
        except OSError as error:
            return f"destination ancestor cannot be inspected: {current}: {error}"
        if current.is_symlink():
            if _allowed_system_alias(current):
                continue
            return f"destination has a symlinked ancestor: {current}"
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


def _open_destination(destination: Path) -> tuple[int, tuple[int, int, int]]:
    flags = os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(destination, flags)
    info = os.fstat(descriptor)
    identity = info.st_dev, info.st_ino, stat.S_IFMT(info.st_mode)
    if identity[2] != stat.S_IFDIR or _path_identity(destination) != identity:
        os.close(descriptor)
        raise OSError(f"destination changed while opening: {destination}")
    return descriptor, identity


def _verify_open_destination(
    destination: Path,
    descriptor: int,
    identity: tuple[int, int, int],
) -> None:
    info = os.fstat(descriptor)
    opened_identity = info.st_dev, info.st_ino, stat.S_IFMT(info.st_mode)
    if (
        opened_identity != identity
        or destination.is_symlink()
        or _path_identity(destination) != identity
    ):
        raise OSError(f"opened destination was replaced: {destination}")


def _create_symlink_exclusive(
    source: Path,
    destination: Path,
    name: str,
    kind: str,
    owned_paths: list[_OwnedPath],
) -> Path:
    return _create_raw_symlink_exclusive(
        str(source.resolve(strict=True)), destination, name, kind, owned_paths
    )


def _create_raw_symlink_exclusive(
    target: str,
    destination: Path,
    name: str,
    kind: str,
    owned_paths: list[_OwnedPath],
) -> Path:
    for _ in range(TEMP_ATTEMPTS):
        candidate = _temporary_path(destination, name, kind)
        try:
            os.symlink(target, candidate, target_is_directory=True)
        except FileExistsError:
            continue
        if not candidate.is_symlink() or os.readlink(candidate) != target:
            raise OSError(f"exclusive {kind} link was substituted: {candidate}")
        owned_paths.append(_OwnedPath(candidate, _path_identity(candidate), target))
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
    owned_paths: list[_OwnedPath],
    *,
    expected_identity: tuple[int, int, int],
    expected_target: str | None,
) -> Path:
    for _ in range(TEMP_ATTEMPTS):
        candidate = _temporary_path(destination, name, kind)
        try:
            os.link(source, candidate, follow_symlinks=False)
        except FileExistsError:
            continue
        candidate_identity = _path_identity(candidate)
        if candidate_identity == expected_identity:
            owned_paths.append(
                _OwnedPath(
                    candidate,
                    candidate_identity,
                    expected_target,
                )
            )
        else:
            source_identity = _path_identity(source)
            if candidate_identity == source_identity:
                owned_paths.append(_OwnedPath(candidate, candidate_identity))
            raise OSError(f"exclusive {kind} hard link has unexpected identity")
        if expected_target is not None and (
            not candidate.is_symlink()
            or os.readlink(candidate) != expected_target
        ):
            raise OSError(f"exclusive {kind} hard link has unexpected target")
        return candidate
    raise FileExistsError(
        errno.EEXIST,
        f"cannot allocate exclusive {kind} link after {TEMP_ATTEMPTS} attempts",
    )


def _prepare_ready_link(
    source: Path,
    destination: Path,
    name: str,
    owned_paths: list[_OwnedPath],
) -> Path:
    expected_target = str(source.resolve(strict=True))
    stage = _create_symlink_exclusive(
        source, destination, name, "stage", owned_paths
    )
    stage_identity = _path_identity(stage)
    if not stage.is_symlink() or os.readlink(stage) != expected_target:
        raise OSError(f"stage link was substituted before hard-linking: {stage}")
    ready = _create_hardlink_exclusive(
        stage,
        destination,
        name,
        "ready",
        owned_paths,
        expected_identity=stage_identity,
        expected_target=expected_target,
    )
    if (
        _path_identity(stage) != stage_identity
        or not stage.is_symlink()
        or os.readlink(stage) != expected_target
        or _path_identity(ready) != stage_identity
        or not ready.is_symlink()
        or os.readlink(ready) != expected_target
    ):
        raise OSError(f"stage or ready link was substituted for {name}")
    _cleanup_owned_path(_owned_record(owned_paths, stage))
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


def _cleanup_owned_path(owned: _OwnedPath) -> None:
    if not _lexists(owned.path):
        return
    if _path_identity(owned.path) != owned.identity:
        raise OSError(f"refusing to clean substituted temporary path: {owned.path}")
    if owned.target is not None and (
        not owned.path.is_symlink()
        or os.readlink(owned.path) != owned.target
    ):
        raise OSError(f"refusing to clean retargeted temporary path: {owned.path}")
    owned.path.unlink()


def _owned_record(owned_paths: list[_OwnedPath], path: Path) -> _OwnedPath:
    for owned in reversed(owned_paths):
        if owned.path == path:
            return owned
    raise OSError(f"temporary path has no ownership record: {path}")


def _retag_owned_path(owned_paths: list[_OwnedPath], path: Path) -> None:
    for index in range(len(owned_paths) - 1, -1, -1):
        if owned_paths[index].path != path:
            continue
        identity = _path_identity(path)
        target = os.readlink(path) if path.is_symlink() else None
        owned_paths[index] = _OwnedPath(path, identity, target)
        return
    raise OSError(f"temporary path has no ownership record: {path}")


def _matches_symlink(
    path: Path,
    identity: tuple[int, int, int],
    target: str,
) -> bool:
    try:
        return (
            path.is_symlink()
            and _path_identity(path) == identity
            and os.readlink(path) == target
        )
    except OSError:
        return False


def _cleanup_owned_paths(
    owned_paths: list[_OwnedPath],
    retained: set[tuple[Path, tuple[int, int, int]]],
    errors: list[str],
) -> BaseException | None:
    pending: BaseException | None = None
    remaining = list(reversed(owned_paths))
    reported: set[Path] = set()
    for _ in range(2):
        retry: list[_OwnedPath] = []
        for owned in remaining:
            if (owned.path, owned.identity) in retained:
                continue
            try:
                _cleanup_owned_path(owned)
            except BaseException as cleanup_error:
                if isinstance(cleanup_error, Exception):
                    if owned.path not in reported:
                        errors.append(
                            f"temporary cleanup failed for {owned.path}: "
                            f"{cleanup_error}"
                        )
                        reported.add(owned.path)
                elif pending is None:
                    pending = cleanup_error
                try:
                    if (
                        _lexists(owned.path)
                        and _path_identity(owned.path) == owned.identity
                    ):
                        retry.append(owned)
                except BaseException as inspection_error:
                    if isinstance(inspection_error, Exception):
                        errors.append(
                            f"temporary cleanup inspection failed for {owned.path}: "
                            f"{inspection_error}"
                        )
                    elif pending is None:
                        pending = inspection_error
        remaining = retry
        if not remaining:
            break
    return pending


def _exchange_restore(
    item: _AppliedLink,
    material: Path,
    material_identity: tuple[int, int, int],
) -> None:
    last_error: Exception | None = None
    for _ in range(2):
        try:
            _atomic_exchange(item.path, material)
        except Exception as error:
            last_error = error
            if _path_identity(item.path) == material_identity:
                return
            if (
                not item.path.is_symlink()
                or _path_identity(item.path) != item.new_identity
                or _path_identity(material) != material_identity
            ):
                raise _ManualRecoveryError(
                    f"manual recovery required for {item.name}: destination or "
                    f"rollback material changed; preserved material at {material}",
                    material,
                    material_identity,
                ) from error
            continue
        if _path_identity(item.path) == material_identity:
            return
        raise OSError(f"atomic rollback verification failed for {item.name}")

    raise _ManualRecoveryError(
        f"manual recovery required for {item.name}: atomic rollback failed; "
        f"preserved material at {material}: {last_error}",
        material,
        material_identity,
    ) from last_error


def _rollback_links(
    applied: list[_AppliedLink],
    errors: list[str],
    owned_paths: list[_OwnedPath],
    retained: set[tuple[Path, tuple[int, int, int]]],
) -> BaseException | None:
    pending: BaseException | None = None
    for item in reversed(applied):
        material: Path | None = None
        material_identity: tuple[int, int, int] | None = None
        try:
            if item.operation == "created":
                if (
                    not item.path.is_symlink()
                    or _path_identity(item.path) != item.new_identity
                ):
                    raise OSError(f"created path is not a symlink: {item.path}")
                item.path.unlink()
                continue

            current_identity = _path_identity(item.path)
            if (
                item.displaced_identity is not None
                and current_identity == item.displaced_identity
            ):
                continue
            if current_identity != item.new_identity or not item.path.is_symlink():
                raise OSError(f"installed path changed before rollback: {item.path}")

            expected_target: str | None = None
            if (
                item.displaced is not None
                and item.displaced_identity is not None
                and _lexists(item.displaced)
                and _path_identity(item.displaced) == item.displaced_identity
            ):
                material = item.displaced
                material_identity = item.displaced_identity
                if item.displaced_identity == item.old_identity:
                    expected_target = item.old_target
            else:
                for candidate in (item.recovery, item.backup):
                    if candidate is None or not _lexists(candidate):
                        continue
                    if (
                        item.old_identity is not None
                        and candidate.is_symlink()
                        and _path_identity(candidate) == item.old_identity
                        and os.readlink(candidate) == item.old_target
                    ):
                        material = candidate
                        material_identity = item.old_identity
                        expected_target = item.old_target
                        break
            if material is None:
                if item.old_target is None:
                    raise OSError(f"rollback target is missing for {item.name}")
                material = _create_raw_symlink_exclusive(
                    item.old_target,
                    item.path.parent,
                    item.name,
                    "rollback",
                    owned_paths,
                )
                material_identity = _path_identity(material)
                expected_target = item.old_target

            assert material_identity is not None
            _exchange_restore(item, material, material_identity)
            try:
                _owned_record(owned_paths, material)
            except OSError:
                pass
            else:
                _retag_owned_path(owned_paths, material)
            if expected_target is not None and (
                not item.path.is_symlink()
                or os.readlink(item.path) != expected_target
            ):
                raise OSError(f"rollback target verification failed for {item.name}")
        except _ManualRecoveryError as rollback_error:
            retained.add(
                (rollback_error.material, rollback_error.material_identity)
            )
            errors.append(f"rollback failed for {item.name}: {rollback_error}")
        except BaseException as rollback_error:
            if material is not None and material_identity is not None:
                retained.add((material, material_identity))
            if isinstance(rollback_error, Exception):
                errors.append(f"rollback failed for {item.name}: {rollback_error}")
            elif pending is None:
                pending = rollback_error
    return pending


def _apply_plan(source: _Source, destination: Path, plan: _Plan) -> _MutationOutcome:
    created_directories: list[Path] = []
    owned_paths: list[_OwnedPath] = []
    applied: list[_AppliedLink] = []
    previous = dict(plan.previous_links)
    errors: list[str] = []
    retained: set[tuple[Path, tuple[int, int, int]]] = set()
    pending: BaseException | None = None
    destination_descriptor: int | None = None
    destination_identity: tuple[int, int, int] | None = None
    committed = False
    try:
        _create_destination(destination, created_directories)
        if destination.is_symlink() or not destination.is_dir():
            raise OSError(f"destination became unsafe: {destination}")
        destination_descriptor, destination_identity = _open_destination(destination)
        for name in sorted((*plan.created, *plan.updated)):
            _verify_open_destination(
                destination, destination_descriptor, destination_identity
            )
            path = destination / name
            operation = "created" if name in plan.created else "updated"
            old_target = previous.get(name)
            expected_target = str((source.root / name).resolve(strict=True))
            if operation == "created":
                if _lexists(path):
                    raise OSError(f"destination changed during install: {path}")
                ready = _prepare_ready_link(
                    source.root / name, destination, name, owned_paths
                )
                new_identity = _path_identity(ready)
                if not _matches_symlink(ready, new_identity, expected_target):
                    raise OSError(f"ready link was substituted before publish: {ready}")
                _verify_open_destination(
                    destination, destination_descriptor, destination_identity
                )
                try:
                    _publish_without_overwrite(ready, path)
                except BaseException:
                    if _matches_symlink(path, new_identity, expected_target):
                        applied.append(
                            _AppliedLink(name, operation, path, new_identity)
                        )
                    raise
                if not _matches_symlink(path, new_identity, expected_target):
                    raise OSError(f"published link was substituted: {path}")
                applied.append(
                    _AppliedLink(name, operation, path, new_identity)
                )
                _cleanup_owned_path(_owned_record(owned_paths, ready))
                continue

            if not path.is_symlink() or os.readlink(path) != old_target:
                raise OSError(f"managed link changed during install: {path}")
            old_identity = _path_identity(path)
            backup = _create_hardlink_exclusive(
                path,
                destination,
                name,
                "backup",
                owned_paths,
                expected_identity=old_identity,
                expected_target=old_target,
            )
            if (
                _path_identity(path) != old_identity
                or not path.is_symlink()
                or os.readlink(path) != old_target
                or _path_identity(backup) != old_identity
            ):
                raise OSError(f"managed link changed while backing up: {path}")
            ready = _prepare_ready_link(
                source.root / name, destination, name, owned_paths
            )
            new_identity = _path_identity(ready)
            if not _matches_symlink(ready, new_identity, expected_target):
                raise OSError(f"ready link was substituted before exchange: {ready}")
            item = _AppliedLink(
                name,
                operation,
                path,
                new_identity,
                old_target=old_target,
                old_identity=old_identity,
                backup=backup,
            )
            _verify_open_destination(
                destination, destination_descriptor, destination_identity
            )
            exchange_error: BaseException | None = None
            try:
                _atomic_exchange(path, ready)
            except BaseException as error:
                exchange_error = error
            if _matches_symlink(path, new_identity, expected_target):
                item.displaced = ready
                item.displaced_identity = _path_identity(ready)
                _retag_owned_path(owned_paths, ready)
                applied.append(item)
            elif exchange_error is not None:
                raise exchange_error
            else:
                raise OSError(f"managed link changed during atomic exchange: {path}")
            if exchange_error is not None:
                raise exchange_error
            if (
                _path_identity(ready) != old_identity
                or not ready.is_symlink()
                or os.readlink(ready) != old_target
            ):
                exchange_back_error: BaseException | None = None
                try:
                    _atomic_exchange(path, ready)
                except BaseException as error:
                    exchange_back_error = error
                if _matches_symlink(ready, new_identity, expected_target):
                    _retag_owned_path(owned_paths, ready)
                if exchange_back_error is not None:
                    raise exchange_back_error
                raise OSError(f"managed link changed during atomic exchange: {path}")
            _cleanup_owned_path(_owned_record(owned_paths, ready))

        updates = [item for item in applied if item.operation == "updated"]
        for item in updates:
            assert item.backup is not None
            item.recovery = _create_hardlink_exclusive(
                item.backup,
                destination,
                item.name,
                "recovery",
                owned_paths,
                expected_identity=item.old_identity,
                expected_target=item.old_target,
            )
        for item in updates:
            assert item.backup is not None
            _cleanup_owned_path(_owned_record(owned_paths, item.backup))
        for item in updates:
            assert item.recovery is not None
            _cleanup_owned_path(_owned_record(owned_paths, item.recovery))
        committed = True
    except BaseException as error:
        if isinstance(error, Exception):
            errors.append(f"installation mutation failed: {error}")
        else:
            pending = error
        rollback_pending = _rollback_links(
            applied,
            errors,
            owned_paths,
            retained,
        )
        if pending is None:
            pending = rollback_pending
    finally:
        if not committed:
            cleanup_pending = _cleanup_owned_paths(
                owned_paths, retained, errors
            )
            if pending is None:
                pending = cleanup_pending
            for directory in reversed(created_directories):
                try:
                    directory.rmdir()
                except BaseException as cleanup_error:
                    if isinstance(cleanup_error, Exception):
                        errors.append(
                            f"destination cleanup failed for {directory}: "
                            f"{cleanup_error}"
                        )
                    elif pending is None:
                        pending = cleanup_error
        if destination_descriptor is not None:
            try:
                os.close(destination_descriptor)
            except BaseException as close_error:
                if isinstance(close_error, Exception):
                    errors.append(f"destination close failed: {close_error}")
                elif pending is None:
                    pending = close_error
    if pending is not None:
        raise pending
    return _MutationOutcome(tuple(errors), ())


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
            planned_created=plan.created,
            planned_updated=plan.updated,
            unchanged=plan.unchanged,
            skipped=plan.skipped,
            collisions=plan.collisions,
            errors=outcome.errors,
            warnings=outcome.warnings,
        )
    return InstallResult(
        created=plan.created,
        updated=plan.updated,
        planned_created=plan.created,
        planned_updated=plan.updated,
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
            f"Applied: created {len(result.created)}, updated {len(result.updated)}; "
            f"unchanged {len(result.unchanged)}, skipped {len(result.skipped)}."
        )
        print(
            f"Planned: create {len(result.planned_created)}, "
            f"update {len(result.planned_updated)}."
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
