from hashlib import sha256
from pathlib import Path


EXCLUDED_SOURCE_DIRECTORIES = {"codex-skills", "docs"}


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
