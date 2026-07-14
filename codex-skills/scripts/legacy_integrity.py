"""Pinned integrity contracts for promoted legacy Codex skills."""

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from types import MappingProxyType
from typing import Iterable, Mapping


@dataclass(frozen=True)
class LegacyIntegrityPin:
    provenance: str
    archived_source_sha256: str
    promoted_input_sha256: str


_PIN_DATA = {
    "gitnexus-cli": (
        "a699a9dd168a68e7357b1704be0ff5ceee30b2a348042789355cca171c060e02",
        "71d686d81713621d9df050e85faedec51749fea88488fc880b681d5876fb0706",
    ),
    "gitnexus-debugging": (
        "4a1e82aa835c52e38227d853c20ef05ea33be1dfb6aa6511474d15357f1d3f2e",
        "e77115bb0c1b0c38aea2b73c60d79bdc6460b3784dd9f37d44f4b9ba7e926c3c",
    ),
    "gitnexus-exploring": (
        "ffafeaa0ce52be079e4d4b3a48c0a166728c009380a243c394c4e08f728527bb",
        "15af2f5550d327d2d36b8a28e96b5b361dabcfd950d249eeff29af5f80f8ac3d",
    ),
    "gitnexus-guide": (
        "40b047beeb9a7c5d47f17426b4061d2c2562c85c11288fa7f8da376d910e4f91",
        "25814aa095be6dc48cc25f027142d2b524fc2cfa748a5189fdede21a79ab1482",
    ),
    "gitnexus-impact-analysis": (
        "a4d6e8003c4a822c380b0e81b2fa0d642612236c734a9d51834e362c4be52f33",
        "70fbc9d1e1e1e9a81545b20f57a286723e2a4301010f00649edf6e886e307b52",
    ),
    "gitnexus-pr-review": (
        "f7bac200a4752191d2e3aa7a2273720ca436d25df88cb2ef48dc19f92ae0934e",
        "063a613a59fe0bba18a946828738ced39a7f1d7f34bd743a79ee5591c3fd22d5",
    ),
    "gitnexus-refactoring": (
        "6aab994ee0266063245245483ee3280645aca66c0c5e56730ffad3f32ecbbc5c",
        "c26e29e19e908eb2644c682d320a1a2cea77d0714d668d2843d634c14a4300b5",
    ),
}

LEGACY_INTEGRITY_PINS: Mapping[str, LegacyIntegrityPin] = MappingProxyType(
    {
        name: LegacyIntegrityPin(
            provenance=f"codex-skills/archived-sources/{name}/SKILL.md",
            archived_source_sha256=digests[0],
            promoted_input_sha256=digests[1],
        )
        for name, digests in _PIN_DATA.items()
    }
)
LEGACY_PROMOTED_PROVENANCE: Mapping[str, str] = MappingProxyType(
    {name: pin.provenance for name, pin in LEGACY_INTEGRITY_PINS.items()}
)
LEGACY_ARCHIVED_SOURCE_SHA256: Mapping[str, str] = MappingProxyType(
    {
        name: pin.archived_source_sha256
        for name, pin in LEGACY_INTEGRITY_PINS.items()
    }
)
LEGACY_PROMOTED_INPUT_SHA256: Mapping[str, str] = MappingProxyType(
    {
        name: pin.promoted_input_sha256
        for name, pin in LEGACY_INTEGRITY_PINS.items()
    }
)


def _digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def validate_legacy_integrity(
    repo_root: Path, names: Iterable[str] | None = None
) -> tuple[str, ...]:
    """Return exact per-skill archive and promoted-input integrity errors."""
    root = Path(repo_root)
    selected = tuple(sorted(names if names is not None else LEGACY_INTEGRITY_PINS))
    errors: list[str] = []
    for name in selected:
        pin = LEGACY_INTEGRITY_PINS.get(name)
        if pin is None:
            errors.append(f"unknown legacy integrity pin: {name}")
            continue

        archive = root / pin.provenance
        if archive.is_symlink() or not archive.is_file():
            errors.append(
                f"legacy archived source is missing or unsafe for {name}: {pin.provenance}"
            )
        else:
            try:
                observed_archive = _digest(archive)
            except OSError as error:
                errors.append(f"legacy archived source cannot be read for {name}: {error}")
            else:
                if observed_archive != pin.archived_source_sha256:
                    errors.append(
                        f"legacy archived source digest mismatch for {name}: expected "
                        f"{pin.archived_source_sha256}, found {observed_archive}"
                    )

        promoted_dir = root / "codex-skills" / "promoted" / name
        promoted_skill = promoted_dir / "SKILL.md"
        if promoted_dir.is_symlink() or not promoted_dir.is_dir():
            errors.append(f"legacy promoted input directory is missing or unsafe for {name}")
            continue
        try:
            entries = tuple(sorted(path.name for path in promoted_dir.iterdir()))
        except OSError as error:
            errors.append(f"legacy promoted input tree cannot be read for {name}: {error}")
            continue
        if entries != ("SKILL.md",):
            errors.append(
                f"legacy promoted input tree mismatch for {name}: expected only "
                f"SKILL.md, found {', '.join(entries) or 'nothing'}"
            )
        if promoted_skill.is_symlink() or not promoted_skill.is_file():
            errors.append(f"legacy promoted input is missing or unsafe for {name}: SKILL.md")
            continue
        try:
            observed_promoted = _digest(promoted_skill)
        except OSError as error:
            errors.append(f"legacy promoted input cannot be read for {name}: {error}")
        else:
            if observed_promoted != pin.promoted_input_sha256:
                errors.append(
                    f"legacy promoted input digest mismatch for {name}: expected "
                    f"{pin.promoted_input_sha256}, found {observed_promoted}"
                )
    return tuple(errors)
