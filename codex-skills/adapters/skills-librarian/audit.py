#!/usr/bin/env python3
"""skills-librarian audit engine (read-only).

Modes:
  audit       integrity report (missing SKILL.md, no name:, name<>folder mismatch, stray files, dead symlinks)
  inventory   `name<TAB>description` per live skill (handles block-scalar YAML descriptions)
  diff-index  live folder vs SKILLS-INDEX.md, expanding the index's slash / -suffix shorthand (APPROXIMATE)

The live folder ~/.codex/skills is the installed source of truth. The dump (~/Desktop/skills:dump) and
~/Desktop/skills-archive-* are NOT live. IGNORE = intentional non-skill folders the index says to keep.

SYNC GATE: the installed shelf may contain managed links into a Git-backed generated collection.
Skills can evolve on other machines, so audit the installed shelf while comparing the parallel
collection repository with origin/main. A repository that is BEHIND is stale: generated links can
silently expose an old count or old skill behavior. Every audit/diff-index fetches and refuses to
certify a generated collection whose repository is behind.
Being AHEAD is normal (new local skills not yet backed up) and is not an error.
Set SKILLS_NO_FETCH=1 to skip the network call (offline); the behind-check still runs on cached refs.
"""
import os, sys, re, subprocess
from pathlib import Path

SK = os.environ.get("SKILLS_DIR", os.path.expanduser("~/.codex/skills"))
INDEX = os.environ.get("SKILLS_INDEX", os.path.expanduser("~/Desktop/Truth/SKILLS-INDEX.md"))

def default_parallel_repo():
    """Resolve a symlinked generated skill back to its repository when possible."""
    resolved = Path(__file__).resolve()
    for parent in resolved.parents:
        if (parent / "codex-skills" / "manifest.yaml").is_file():
            return str(parent)
    return os.path.expanduser("~/claude-skills")

REPO = os.environ.get("CODEX_SKILLS_REPO", default_parallel_repo())
# Intentional non-skill folders (support bundles etc.) — index-blessed, not cruft. Don't flag/quarantine.
#   heygen-skills — source bundle the two HeyGen skills symlink into.
#   codex-skills  — the Codex bridge (manifest/adapters/promoted/tests): mirrors these skills to Codex so
#                   Brent can keep working when Claude usage limits bite. Blessed 2026-07-13.
#   docs          — repo docs (docs/superpowers/plans, specs). Not a skill; never was.
IGNORE = {"heygen-skills", "codex-skills", "docs"}
# Repo/OS metadata — the shelf is a git-backed backup; these are infrastructure, never skills or cruft.
REPO_META = {".git", ".gitignore", ".gitattributes", ".github", ".DS_Store", "__pycache__"}
# Intentional root-level docs (not skills, not cruft) — allowed at the shelf root.
ROOT_DOCS = {"README.md", "AGENTS-CATALOG.md"}

def frontmatter(path):
    """Return dict of top-level frontmatter keys; description handles >|block scalars."""
    try:
        lines = open(path, encoding="utf-8", errors="ignore").read().splitlines()
    except Exception:
        return {}
    if not lines or lines[0].strip() != "---":
        return {}
    fm = {}
    i, key = 1, None
    while i < len(lines):
        ln = lines[i]
        if ln.strip() == "---":
            break
        m = re.match(r"^([A-Za-z0-9_]+):\s?(.*)$", ln)
        if m:
            key, val = m.group(1), m.group(2)
            if val.strip() in (">", "|", ">-", "|-", "|+", ">+", ""):
                # block scalar: gather following more-indented lines
                buf, j = [], i + 1
                while j < len(lines) and (lines[j].startswith((" ", "\t")) or lines[j].strip() == ""):
                    if lines[j].strip() == "---":
                        break
                    buf.append(lines[j].strip())
                    j += 1
                fm[key] = " ".join(x for x in buf if x).strip()
                i = j
                continue
            fm[key] = val.strip().strip('"')
        i += 1
    return fm

def git(*a, timeout=25):
    """Run git in the parallel generated-shelf repository. Never raises."""
    try:
        p = subprocess.run(("git", "-C", REPO) + a, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout.strip()
    except Exception:
        return 1, ""

def sync_check():
    """Is the live shelf current with its mirror? Returns (level, message).

    level: 'ok' | 'info' | 'issue' | 'unverified'
    BEHIND origin/main => 'issue': the shelf is missing skills that exist on another machine.
    AHEAD only         => 'info': local skills not yet backed up. Normal (and true right after
                          backup.sh --confirm, which parks the tree on a librarian-sync-* branch).
    """
    if git("rev-parse", "--git-dir")[0] != 0:
        return "unverified", f"SYNC UNVERIFIED — parallel collection is not a git repo: {REPO}"

    degraded = ""
    if os.environ.get("SKILLS_NO_FETCH") == "1":
        degraded = "network fetch skipped by SKILLS_NO_FETCH=1"
    else:
        rc, _ = git("fetch", "--quiet", "origin", timeout=45)
        if rc != 0:
            degraded = "origin fetch failed"

    # Resolve the mirror's default branch; fall back to origin/main.
    rc, head = git("symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD")
    ref = head if rc == 0 and head else "origin/main"
    if git("rev-parse", "--verify", "--quiet", ref)[0] != 0:
        context = f" after {degraded}" if degraded else ""
        return "unverified", f"SYNC UNVERIFIED — no {ref} to compare against{context}"

    rc, behind = git("rev-list", "--count", f"HEAD..{ref}")
    rc2, ahead = git("rev-list", "--count", f"{ref}..HEAD")
    if rc != 0 or rc2 != 0:
        context = f" after {degraded}" if degraded else ""
        return "unverified", f"SYNC UNVERIFIED — could not compare HEAD to {ref}{context}"
    try:
        behind, ahead = int(behind), int(ahead)
    except ValueError:
        return "unverified", f"SYNC UNVERIFIED — non-numeric rev-list result for {ref}"

    degraded_suffix = (
        f"; {degraded}; cached comparison only, so upstream freshness is unverified"
        if degraded
        else ""
    )

    if behind:
        return "issue", (f"SHELF IS STALE — {behind} commit(s) behind {ref}"
                         + (f" (and {ahead} ahead)" if ahead else "")
                         + f". Generated skills from newer commits are MISSING locally; this audit "
                           f"cannot certify the shelf. Fix first:  git -C {REPO} pull --ff-only"
                         + degraded_suffix)
    if ahead:
        return "info", (f"{ahead} commit(s) ahead of {ref} — local skills not yet backed up "
                        f"(normal; run backup.sh){degraded_suffix}")
    if degraded:
        return "info", (
            f"cached comparison confirms HEAD matches {ref}; {degraded}; "
            "upstream freshness is unverified"
        )
    return "ok", f"in sync with {ref}"

def live_skills():
    out = {}
    for n in sorted(os.listdir(SK)):
        if n in REPO_META or n.startswith("."):
            continue
        d = os.path.join(SK, n)
        if os.path.isdir(d):
            out[n] = d
    return out

def expand_index_names(text):
    """Extract every skill name from the index, expanding `**a / -b / -c**` shorthand."""
    names = set()
    for span in re.findall(r"\*\*([^*]+)\*\*", text):
        prefix = None
        for tok in span.split("/"):
            tok = tok.strip().strip("+").strip()
            if not tok:
                continue
            if tok.startswith("-"):
                if prefix:
                    names.add(prefix + tok)
            else:
                names.add(tok)
                prefix = tok.rsplit("-", 1)[0] if "-" in tok else tok
    return {n for n in names if re.match(r"^[a-z0-9][a-z0-9:_-]*$", n)}

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "audit"
    live = live_skills()

    if mode == "audit":
        issues, ignored = [], []
        for n, d in live.items():
            sm = os.path.join(d, "SKILL.md")
            if n in IGNORE:
                ignored.append(n); continue
            if not os.path.isfile(sm):
                issues.append(f"NO SKILL.md: {n}"); continue
            fm = frontmatter(sm)
            nm = fm.get("name", "")
            if not nm:
                issues.append(f"no name: field: {n}")
            elif nm != n:
                issues.append(f"MISMATCH folder={n} name:={nm}")
        for f in sorted(os.listdir(SK)):
            if f in REPO_META or f in ROOT_DOCS or f.startswith("."):
                continue
            p = os.path.join(SK, f)
            if not os.path.isdir(p):
                issues.append(f"stray file (not a skill folder): {f}")
            if os.path.islink(p) and not os.path.exists(p):
                issues.append(f"dead symlink: {f}")
        level, msg = sync_check()
        print(f"Live skills dir: {SK}")
        print(f"Total skill folders: {len(live)}\n== MIRROR SYNC ==")
        print({"ok": "  ✓ ", "info": "  · ", "issue": "  ✗ ", "unverified": "  ✗ "}[level] + msg)
        print("== INTEGRITY ==")
        for x in issues: print(f"  ✗ {x}")
        if not issues: print("  ✓ clean — 0 integrity issues")
        if ignored: print(f"  (ignored intentional non-skill folders: {', '.join(ignored)})")
        sync_failure = level in ("issue", "unverified")
        total = len(issues) + (1 if sync_failure else 0)
        print(f"\nissues: {total}" + ("  (1 = mirror sync gate; the count above is NOT certified)" if sync_failure else ""))
        sys.exit(1 if total else 0)

    elif mode == "inventory":
        for n, d in live.items():
            if n in IGNORE: continue
            fm = frontmatter(os.path.join(d, "SKILL.md"))
            desc = re.sub(r"\s+", " ", fm.get("description", "")).strip()[:160]
            print(f"{fm.get('name', n)}\t{desc}")

    elif mode == "diff-index":
        if not os.path.isfile(INDEX):
            print(f"INDEX not found: {INDEX}"); sys.exit(1)
        level, msg = sync_check()
        if level in ("issue", "info", "unverified"):
            print(f"== MIRROR SYNC ==\n  {'✗' if level in ('issue', 'unverified') else '·'} {msg}")
            if level in ("issue", "unverified"):
                print("  REFUSING to diff without a verified current shelf. Restore comparison refs or pull, then re-run.")
                sys.exit(1)
            print()
        indexed = expand_index_names(open(INDEX, encoding="utf-8", errors="ignore").read()) - IGNORE
        liveset = set(live) - IGNORE
        new = sorted(liveset - indexed)
        stale = sorted(indexed - liveset)
        print("== NEW (live but not found in index) ==")
        for x in new: print(f"  + {x}")
        print("== STALE (in index but not live) ==")
        for x in stale: print(f"  - {x}")
        print(f"== counts ==\n  live={len(liveset)}  indexed_names_parsed={len(indexed)}  new={len(new)}  stale={len(stale)}")
        print("NOTE: index uses grouped shorthand; this expansion is APPROXIMATE — confirm by reading the index.")

    else:
        print("usage: audit.py {audit | inventory | diff-index}"); sys.exit(1)

if __name__ == "__main__":
    main()
