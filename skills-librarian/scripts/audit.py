#!/usr/bin/env python3
"""skills-librarian audit engine (read-only).

Modes:
  audit       integrity report (missing SKILL.md, no name:, name<>folder mismatch, stray files, dead symlinks)
  inventory   `name<TAB>description` per live skill (handles block-scalar YAML descriptions)
  diff-index  live folder vs SKILLS-INDEX.md, expanding the index's slash / -suffix shorthand (APPROXIMATE)

The live folder ~/.claude/skills is the source of truth. The dump (~/Desktop/skills:dump) and
~/Desktop/skills-archive-* are NOT live. IGNORE = intentional non-skill folders the index says to keep.

SYNC GATE: the shelf is a git work tree backed by the mirror repo, and skills get authored on OTHER
machines. A shelf that is BEHIND origin/main is a stale shelf — auditing it reports a skill count that
is a lie, and indexing it silently omits skills that exist. (2026-07-13: `page-rethink`, authored on
another box, was absent locally; the audit called the shelf clean and the index was written one skill
short.) So every audit/diff-index fetches and refuses to certify a shelf that is behind.
Being AHEAD is normal (new local skills not yet backed up) and is not an error.
Set SKILLS_NO_FETCH=1 to skip the network call (offline); the behind-check still runs on cached refs.
"""
import os, sys, re, subprocess

SK = os.environ.get("SKILLS_DIR", os.path.expanduser("~/.claude/skills"))
INDEX = os.environ.get("SKILLS_INDEX", os.path.expanduser("~/Desktop/Truth/SKILLS-INDEX.md"))
# Intentional non-skill folders (support bundles etc.) — index-blessed, not cruft. Don't flag/quarantine.
IGNORE = {"heygen-skills"}
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
    """Run git in the shelf. Returns (rc, stdout). Never raises."""
    try:
        p = subprocess.run(("git", "-C", SK) + a, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout.strip()
    except Exception:
        return 1, ""

def sync_check():
    """Is the live shelf current with its mirror? Returns (level, message).

    level: 'ok' | 'info' | 'issue' | 'skip'
    BEHIND origin/main => 'issue': the shelf is missing skills that exist on another machine.
    AHEAD only         => 'info': local skills not yet backed up. Normal (and true right after
                          backup.sh --confirm, which parks the tree on a librarian-sync-* branch).
    """
    if git("rev-parse", "--git-dir")[0] != 0:
        return "skip", "shelf is not a git repo — no mirror to compare against"

    if os.environ.get("SKILLS_NO_FETCH") != "1":
        rc, _ = git("fetch", "--quiet", "origin", timeout=45)
        if rc != 0:
            return "info", "could not reach origin (offline?) — comparing against CACHED refs; a newer skill may exist upstream"

    # Resolve the mirror's default branch; fall back to origin/main.
    rc, head = git("symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD")
    ref = head if rc == 0 and head else "origin/main"
    if git("rev-parse", "--verify", "--quiet", ref)[0] != 0:
        return "skip", f"no {ref} to compare against"

    rc, behind = git("rev-list", "--count", f"HEAD..{ref}")
    rc2, ahead = git("rev-list", "--count", f"{ref}..HEAD")
    if rc != 0 or rc2 != 0:
        return "info", f"could not compare HEAD to {ref}"
    behind, ahead = int(behind or 0), int(ahead or 0)

    if behind:
        return "issue", (f"SHELF IS STALE — {behind} commit(s) behind {ref}"
                         + (f" (and {ahead} ahead)" if ahead else "")
                         + f". Skills authored elsewhere are MISSING locally; this audit and the index "
                           f"would both undercount. Fix first:  git -C {SK} pull --ff-only")
    if ahead:
        return "info", f"{ahead} commit(s) ahead of {ref} — local skills not yet backed up (normal; run backup.sh)"
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
        print({"ok": "  ✓ ", "info": "  · ", "issue": "  ✗ ", "skip": "  – "}[level] + msg)
        print("== INTEGRITY ==")
        for x in issues: print(f"  ✗ {x}")
        if not issues: print("  ✓ clean — 0 integrity issues")
        if ignored: print(f"  (ignored intentional non-skill folders: {', '.join(ignored)})")
        stale_shelf = level == "issue"
        total = len(issues) + (1 if stale_shelf else 0)
        print(f"\nissues: {total}" + ("  (1 = stale shelf; the count above is NOT trustworthy)" if stale_shelf else ""))
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
        if level in ("issue", "info", "skip"):
            print(f"== MIRROR SYNC ==\n  {'✗' if level == 'issue' else '·'} {msg}")
            if level == "issue":
                print("  REFUSING to diff a stale shelf — the index would be written short. Pull, then re-run.")
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
