#!/usr/bin/env python3
"""Veterans benefits-gap lead pull — mine Reddit + X + TikTok (keyless) -> tier -> dated file.

Sibling of the SSDI allsup_pull.py, tuned for the veterans-benefits-gap vertical.
Same hard-won recipe: grade on REACHABILITY (a public profile counts), NEVER run
the heavy resolver, the profile IS the channel (Allsup does outreach). Writes
~/Desktop/VETERANS-LEADS-<date>.{md,csv} with columns matching build_book.py.

Usage:
  python3 veterans_pull.py                    # mine + tier -> ~/Desktop/VETERANS-LEADS-<today>
  python3 veterans_pull.py --tier-only PATH   # skip mining; tier an existing leads.jsonl
  python3 veterans_pull.py --full --days 30
"""
import argparse, csv, datetime, html, json, os, re, subprocess

VERTICAL = "veterans-benefits-gap"
SURFACES = ["reddit", "x"]  # Reddit + X only — TikTok dropped (creator/coach noise)
DEFAULT_LEADS = os.path.expanduser("~/Desktop/Datamine-repo/spike/veterans-leads")

# Drop: helping a relative, pros/creators/orgs, already fully rated & thankful.
EXCLUDE = re.compile(r'\b(my (buddy|friend|dad|father|mom|husband|wife|son|daughter|brother|sister)|'
                     r'i.?m a (vso|attorney|lawyer|agent|rep)|as a vso|our clients|our firm|'
                     r'link in bio|dm me for|we help veterans|100% p&t and (grateful|thankful))\b', re.I)
# Handles that read as clinics / creators / firms, not individual veterans.
EXCLUDE_HANDLE = re.compile(r'(clinic|law|legal|vso|attorney|benefits|claims|disability|'
                            r'veteranaid|gov|official|media|network)', re.I)

# BEST — owed but not getting it: denied / appealing / under-rated / never filed.
BEST = re.compile(r'\b(denied|denial|appeal\w*|higher.level review|hlr|board of veterans|'
                  r'never (filed|applied)|didn.?t (know|think) i (qualified|could)|should.?ve filed|'
                  r'under.?rated|rating too low|lowball\w*|0 ?%|zero percent|deserve|'
                  r'reopen\w* (a )?claim|owed|back pay)\b', re.I)
# BETTER — in motion toward filing: how-to-file / evidence / C&P / in process.
BETTER = re.compile(r'\b(how (do|to) i? ?file|start(ing)? a claim|filing (a|my) claim|'
                    r'nexus letter|c&p exam|gathering evidence|pending|waiting|submitted|'
                    r'intent to file|secondary (claim|condition)|increase)\b', re.I)
# GOOD — eligibility / PACT / rating questions (softer intent but real).
GOOD = re.compile(r'\b(pact act|burn pit|agent orange|camp lejeune|gulf war|toxic exposure|'
                  r'am i eligible|do i qualify|what rating|rating question|va math|'
                  r'combined rating|how does va)\b', re.I)
DENS = re.compile(r'\b(denied|appeal|underrated|lowball|never filed|deserve|owed|pact|'
                  r'burn pit|agent orange|0 ?%|nexus|c&p|back pay|desperate)\b', re.I)
# A real lead speaks in FIRST PERSON about their OWN claim. Creators/coaches speak
# in 2nd/3rd person ("veterans are...", "this veteran", "you were denied") — this
# gate kills the TikTok creator noise without excluding actual claimants.
FIRST_PERSON = re.compile(r"(\bi\b|\bi['’]?m\b|\bi['’]?ve\b|\bmy\b|\bme\b|\bmyself\b|\bmine\b)", re.I)


def export_oxylabs():
    if os.environ.get("OXYLABS_USERNAME") and os.environ.get("OXYLABS_PASSWORD"):
        return
    spec = os.environ.get("REFINE_ENV_FILES")
    files = spec.split(os.pathsep) if spec else [os.path.expanduser("~/Desktop/GitSync/kloop.env")]
    for path in files:
        try:
            lines = open(os.path.expanduser(path)).read().splitlines()
        except FileNotFoundError:
            continue
        for ln in lines:
            m = re.match(r'^\s*(OXYLABS_USERNAME|OXYLABS_PASSWORD)=(.*)$', ln)
            if m and m.group(1) not in os.environ:
                os.environ[m.group(1)] = m.group(2).strip().strip('"').strip("'")


def find_datamine():
    for c in [os.environ.get("DATAMINE_BIN"),
              os.path.expanduser("~/Datamine/.venv/bin/datamine"),
              os.path.expanduser("~/Desktop/Datamine-repo/.venv/bin/datamine"),
              "datamine"]:
        if c and (os.path.sep not in c or os.path.exists(c)):
            return c
    return "datamine"


def mine(days, out_prefix):
    export_oxylabs()
    os.makedirs(os.path.dirname(out_prefix), exist_ok=True)
    cmd = [find_datamine(), "--vertical", VERTICAL, "--surfaces", *SURFACES,
           "--days", str(days), "--no-ledger", "--out", out_prefix]
    print("mining:", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)
    return out_prefix + ".jsonl"


def clean(q):
    q = re.sub(r'<!--.*?-->', ' ', q); q = re.sub(r'<[^>]+>', ' ', q); q = html.unescape(q)
    return re.sub(r'\s+', ' ', q).strip()


def reach(r):
    if r['src'] == 'reddit':
        return "https://www.reddit.com/user/" + r['h'].lstrip('/').replace('u/', '')
    if r['src'] == 'x':
        return "https://x.com/" + r['h'].lstrip('@')
    if r['src'] == 'tiktok':
        return "https://www.tiktok.com/@" + r['h'].lstrip('@')
    return r['url']


def tier(r):
    q = r['q']
    if len(q) < 70 or EXCLUDE.search(q) or EXCLUDE_HANDLE.search(r['h']):
        return None
    if not FIRST_PERSON.search(q):   # creators speak about veterans, not as one
        return None
    if BEST.search(q): return 'best'
    if BETTER.search(q): return 'better'
    if GOOD.search(q): return 'good'
    return None


def load(path):
    best = {}
    for line in open(path, encoding="utf-8"):
        if not line.strip():
            continue
        d = json.loads(line)
        h = (d.get("handle") or "").strip()
        if not h:
            continue
        q = clean(d.get("text") or "")
        if h not in best or len(q) > len(best[h]['q']):
            best[h] = {'h': h, 'src': d.get('source', ''), 'url': d.get('url', ''), 'q': q}
    return list(best.values())


def main():
    ap = argparse.ArgumentParser(description="Veterans benefits-gap lead pull (Allsup)")
    ap.add_argument("--tier-only", metavar="LEADS_JSONL", help="skip mining; tier this file")
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--best", type=int, default=4)
    ap.add_argument("--better", type=int, default=3)
    ap.add_argument("--good", type=int, default=3)
    ap.add_argument("--full", action="store_true", help="emit the whole tiered pool")
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    ap.add_argument("--outdir", default=os.path.expanduser("~/Desktop"))
    a = ap.parse_args()

    leads = a.tier_only or (mine(a.days, DEFAULT_LEADS))
    pool = load(leads)
    buckets = {'best': [], 'better': [], 'good': []}
    for r in pool:
        t = tier(r)
        if t:
            buckets[t].append(r)
    for t in buckets:
        buckets[t].sort(key=lambda r: -len(DENS.findall(r['q'])))
    caps = {'best': a.best, 'better': a.better, 'good': a.good}
    pick = {t: (v if a.full else v[:caps[t]]) for t, v in buckets.items()}

    label = {'best': 'BEST — owed but not getting it (denied / appealing / under-rated / never filed)',
             'better': 'BETTER — in motion (filing / evidence / C&P / secondary)',
             'good': 'GOOD — eligibility / PACT Act / rating questions'}
    md = os.path.join(a.outdir, f"VETERANS-LEADS-{a.date}.md")
    cs = os.path.join(a.outdir, f"VETERANS-LEADS-{a.date}.csv")
    with open(md, "w") as f:
        f.write("# Veterans Lead Batch — benefits gap (Reddit + X + TikTok)\n\n")
        f.write(f"**From:** Brent Bryson · **Date:** {a.date} · "
                f"**Status:** {'full pool' if a.full else f'{a.best} best / {a.better} better / {a.good} good'}\n\n")
        f.write("Real veterans who **publicly posted** about VA benefits they're owed but not getting — "
                "never filed, denied, under-rated, or newly eligible (PACT Act) — tiered by need. Each "
                "reachable via at least one public channel. We do not contact anyone — outreach is Allsup's job.\n\n---\n\n")
        for t in ['best', 'better', 'good']:
            f.write(f"# {label[t]}\n\n")
            for r in pick[t]:
                f.write(f"## {r['h']}  ({r['src']})\n> \"{r['q'][:300]}\"\n\n"
                        f"- **Source post:** {r['url']}\n- **Reachable:** {reach(r)}\n\n")
    with open(cs, "w", newline="") as f:
        w = csv.writer(f); w.writerow(['tier', 'handle', 'source', 'quote', 'source_post', 'reachable_profile'])
        for t in ['best', 'better', 'good']:
            for r in pick[t]:
                w.writerow([t, r['h'], r['src'], r['q'][:400], r['url'], reach(r)])

    print(f"pool: best={len(buckets['best'])} better={len(buckets['better'])} good={len(buckets['good'])}")
    print(f"wrote {sum(len(v) for v in pick.values())} leads -> {md} and {cs}")


if __name__ == "__main__":
    main()
