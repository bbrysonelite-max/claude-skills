#!/usr/bin/env python3
"""Never-repeat ledger helper for the tiger-leader-hunt skill.

Tracks leader handles already surfaced, keyed as ``platform:handle`` so the
same name on two platforms is treated as two distinct candidates.

Usage:
  dedup.py --seen seen.txt --check "tiktok:fezknowzai,ig:toddfalcone"
      -> prints the ids NOT already in seen.txt (one per line)
  dedup.py --seen seen.txt --add "tiktok:fezknowzai,ig:toddfalcone"
      -> appends the new ids to seen.txt, prints the ones it added
"""
import argparse
import sys
from pathlib import Path


def normalize(raw: str) -> str:
    """Lowercase, trim, drop a leading @ on the handle. Keep platform:handle shape."""
    s = raw.strip().lower()
    if not s:
        return ""
    if ":" in s:
        platform, handle = s.split(":", 1)
        return f"{platform.strip()}:{handle.strip().lstrip('@')}"
    return s.lstrip("@")


def load_seen(path: Path) -> set:
    if not path.exists():
        return set()
    out = set()
    for line in path.read_text().splitlines():
        if line.lstrip().startswith("#"):
            continue
        n = normalize(line)
        if n:
            out.add(n)
    return out


def new_ids(candidates, seen) -> list:
    """Return normalized candidates not in `seen`, deduped within the batch, order-preserving."""
    seen_set = set(seen)
    out = []
    for c in candidates:
        n = normalize(c)
        if n and n not in seen_set:
            out.append(n)
            seen_set.add(n)
    return out


def add_ids(path: Path, candidates) -> list:
    """Append new normalized candidates to the ledger file. Return what was added."""
    fresh = new_ids(candidates, load_seen(path))
    if fresh:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a") as f:
            for n in fresh:
                f.write(n + "\n")
    return fresh


def _split(raw: str) -> list:
    return [c for c in raw.split(",") if c.strip()]


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="tiger-leader-hunt ledger helper")
    p.add_argument("--seen", required=True, help="path to seen.txt ledger")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", help="comma-separated ids; print those NOT in the ledger")
    g.add_argument("--add", help="comma-separated ids; append new ones, print them")
    args = p.parse_args(argv)
    path = Path(args.seen).expanduser()

    if args.check is not None:
        for n in new_ids(_split(args.check), load_seen(path)):
            print(n)
    else:
        for n in add_ids(path, _split(args.add)):
            print(n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
