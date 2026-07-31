#!/usr/bin/env python3

import argparse
import json
import sys
from pathlib import Path

try:
    from scripts.install import install
except ModuleNotFoundError:  # Support direct execution as scripts/sync_active.py.
    from install import install  # type: ignore[no-redef]


PROFILE_FILENAME = "active-profile.json"


def load_inactive_skills(profile: Path) -> tuple[str, ...]:
    try:
        data = json.loads(profile.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"active profile cannot be read: {profile}: {error}") from error
    if data.get("schema_version") != 1:
        raise ValueError(f"active profile has unsupported schema: {profile}")
    entries = data.get("inactive_skills")
    if not isinstance(entries, list):
        raise ValueError(f"active profile must contain inactive_skills: {profile}")
    names: list[str] = []
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("name"), str):
            raise ValueError(f"active profile has an invalid inactive skill: {profile}")
        name = entry["name"]
        if not name or name in names:
            raise ValueError(f"active profile has an empty or duplicate skill: {name!r}")
        names.append(name)
    return tuple(names)


def _print_result(result, *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        return
    print(
        f"Applied: created {len(result.created)}, updated {len(result.updated)}; "
        f"unchanged {len(result.unchanged)}, skipped {len(result.skipped)}, "
        f"excluded {len(result.excluded)}."
    )
    print(
        f"Planned: create {len(result.planned_created)}, "
        f"update {len(result.planned_updated)}."
    )
    if result.excluded:
        print("Inactive: " + ", ".join(result.excluded))
    for name in result.collisions:
        print(f"Collision: {name}", file=sys.stderr)
    for error in result.errors:
        print(f"Error: {error}", file=sys.stderr)
    for warning in result.warnings:
        print(f"Warning: {warning}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Sync the generated Codex collection using its active profile."
    )
    parser.add_argument("--source", type=Path)
    parser.add_argument("--dest", type=Path)
    parser.add_argument("--profile", type=Path)
    parser.add_argument("--skip-existing", action="append", default=[])
    parser.add_argument("--exclude", action="append", default=[])
    parser.add_argument("--previous-source", action="append", type=Path, default=[])
    parser.add_argument("--include-inactive", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    source = args.source or Path(__file__).resolve().parents[1] / "skills"
    profile = args.profile or source.parent / PROFILE_FILENAME
    try:
        inactive = () if args.include_inactive else load_inactive_skills(profile)
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    exclusions = tuple(dict.fromkeys((*inactive, *args.exclude)))
    result = install(
        source,
        args.dest,
        skip_existing=tuple(args.skip_existing),
        exclude=exclusions,
        previous_sources=tuple(args.previous_source),
        dry_run=args.dry_run,
    )
    _print_result(result, as_json=args.json)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
