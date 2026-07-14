#!/usr/bin/env python3
"""Track 1 — Reddit fear-phrase mining (SSDI/SSI work-fear vertical).

Reddit search.json is 403 from this network; Atom RSS works keyless.
Site-wide search per fear phrase + sub-scoped search in target communities,
then approximate comment counts for high-scoring threads via thread RSS.

Output: track1_reddit.csv + density summary on stdout.
"""
import csv
import re
import sys
import time
import urllib.parse
import urllib.request

try:
    import defusedxml.ElementTree as ET
    from xml.etree.ElementTree import ParseError
except ImportError:  # stdlib fallback (Py 3.7.1+ blocks entity-expansion attacks in ET)
    import xml.etree.ElementTree as ET
    from xml.etree.ElementTree import ParseError
from pathlib import Path

WORKDIR = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else Path.home() / "Desktop/signal-mine"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
ATOM = "{http://www.w3.org/2005/Atom}"

PHRASES = [
    "will I lose SSDI if I work",
    "can I work while on SSDI",
    "can I work while on SSI",
    "trial work period",
    "Ticket to Work",
    "SSDI overpayment",
    "afraid to work on disability",
    "how much can I earn on SSDI",
    "will I lose disability if I work",
]
TARGET_SUBS = ["SSDI", "SocialSecurity", "disability", "SSI", "SSDI_SSI", "Ticket2Work"]
SUB_QUERIES = ["work", "trial work period", "ticket to work"]

CORE = re.compile(r"(lose|losing|keep|cut off|taken? away).{0,40}(ssdi|ssi|disability|benefits|medicare|medicaid).{0,60}(work|job)|"
                  r"(work|job).{0,60}(lose|losing|keep|cut off).{0,40}(ssdi|ssi|disability|benefits|medicare|medicaid)|"
                  r"can i work while on", re.I | re.S)
PROGRAM = re.compile(r"ticket to work|trial work period|twp\b|wipa\b|overpayment|substantial gainful|sga\b|work incentive", re.I)
IMPLIED = re.compile(r"(disab|ssdi|ssi)\w*.{0,80}(job|work|hire|employ)|(job|work|hire|employ)\w*.{0,80}(disab|ssdi|ssi)", re.I | re.S)


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read()


def parse_feed(raw):
    out = []
    try:
        root = ET.fromstring(raw)
    except ParseError:
        return out
    for e in root.iter(f"{ATOM}entry"):
        title = (e.findtext(f"{ATOM}title") or "").strip()
        link = ""
        for l in e.iter(f"{ATOM}link"):
            link = l.attrib.get("href", "")
        cat = e.find(f"{ATOM}category")
        sub = cat.attrib.get("term", "") if cat is not None else ""
        content = (e.findtext(f"{ATOM}content") or "")
        updated = (e.findtext(f"{ATOM}updated") or "")[:10]
        out.append({"title": title, "url": link, "subreddit": sub,
                    "content": content, "date": updated})
    return out


def score(title, content):
    text = f"{title}\n{content}"
    matched = []
    s = 0
    if CORE.search(text):
        s, matched = 10, [CORE.search(text).group(0)[:80]]
    elif PROGRAM.search(text):
        s, matched = 8, sorted(set(m.lower() for m in PROGRAM.findall(text)))[:4]
    elif IMPLIED.search(text):
        s = 6
    return s, "; ".join(m if isinstance(m, str) else " ".join(filter(None, m)) for m in matched)


def thread_id(url):
    m = re.search(r"/comments/([a-z0-9]+)/", url)
    return m.group(1) if m else url


def main():
    seen = {}
    searches = []
    for p in PHRASES:
        q = urllib.parse.quote(p)
        searches.append((p, f"https://www.reddit.com/search.rss?q={q}&sort=new&t=month&limit=25"))
    for sub in TARGET_SUBS:
        for q in SUB_QUERIES:
            qq = urllib.parse.quote(q)
            searches.append((f"r/{sub}: {q}",
                             f"https://www.reddit.com/r/{sub}/search.rss?q={qq}&restrict_sr=1&sort=new&t=month&limit=25"))

    for label, url in searches:
        try:
            entries = parse_feed(fetch(url))
        except Exception as e:
            print(f"  FAIL {label}: {type(e).__name__}", flush=True)
            entries = []
        fresh = 0
        for ent in entries:
            tid = thread_id(ent["url"])
            s, phrases_found = score(ent["title"], ent["content"])
            if s == 0:
                continue
            if tid in seen:
                seen[tid]["found_via"] += f" | {label}"
                continue
            ent["score"] = s
            ent["signal_phrase"] = phrases_found
            ent["found_via"] = label
            seen[tid] = ent
            fresh += 1
        print(f"  {label}: {len(entries)} entries, {fresh} new signal threads", flush=True)
        time.sleep(1.2)

    # approximate comment counts for score>=8 threads via thread RSS
    hot = [e for e in seen.values() if e["score"] >= 8]
    print(f"\ncomment-count pass on {len(hot)} threads (score>=8)...", flush=True)
    for i, ent in enumerate(hot, 1):
        try:
            raw = fetch(ent["url"].rstrip("/") + ".rss?limit=100")
            n = max(0, len(parse_feed(raw)) - 1)  # first entry is the post itself
            ent["comments_approx"] = n
        except Exception:
            ent["comments_approx"] = ""
        if i % 15 == 0:
            print(f"  {i}/{len(hot)}", flush=True)
        time.sleep(1.0)

    rows = sorted(seen.values(), key=lambda e: (-e["score"], e["subreddit"]))
    out = WORKDIR / "track1_reddit.csv"
    cols = ["subreddit", "url", "title", "signal_phrase", "date",
            "comments_approx", "score", "action", "found_via"]
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            r.setdefault("comments_approx", "")
            r["action"] = "outreach-map" if r["score"] >= 8 else "monitor"
            w.writerow(r)

    print(f"\nwrote {len(rows)} signal threads -> {out}")
    dens = {}
    for r in rows:
        k = r["subreddit"] or "(unknown)"
        d = dens.setdefault(k, {"threads": 0, "s10": 0, "s8": 0})
        d["threads"] += 1
        if r["score"] == 10:
            d["s10"] += 1
        elif r["score"] == 8:
            d["s8"] += 1
    print("\ndensity by subreddit (threads / score-10 / score-8):")
    for k, d in sorted(dens.items(), key=lambda x: -x[1]["threads"])[:15]:
        print(f"  {k}: {d['threads']} / {d['s10']} / {d['s8']}")


if __name__ == "__main__":
    main()
