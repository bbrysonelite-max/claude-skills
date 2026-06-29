#!/usr/bin/env python3
"""Track 2 — YouTube creator mining via ScrapeCreators (SSDI/SSI work-fear).

Searches the vertical's YouTube queries, scores video titles on the signal
rubric, rolls up channel density, and pulls top comments on the strongest
videos to surface common questions.

Output: track2_youtube.csv (videos) + channel summary on stdout.
"""
import csv
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

WORKDIR = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else Path.home() / "Desktop/signal-mine"
ENV = Path.home() / ".config/last30days/.env"
BASE = "https://api.scrapecreators.com/v1/youtube"

QUERIES = [
    "Ticket to Work explained",
    "SSDI work rules",
    "SSI work rules",
    "trial work period",
    "working while disabled",
    "losing Medicare Medicaid working",
]

CORE = re.compile(r"(lose|losing|keep|cut off|taken? away).{0,40}(ssdi|ssi|disability|benefits|medicare|medicaid).{0,60}(work|job)|"
                  r"(work|job).{0,60}(lose|losing|keep|cut off).{0,40}(ssdi|ssi|disability|benefits|medicare|medicaid)|"
                  r"can (i|you) work while on", re.I)
PROGRAM = re.compile(r"ticket to work|trial work period|twp\b|wipa\b|overpayment|substantial gainful|sga\b|work incentive", re.I)
IMPLIED = re.compile(r"(disab|ssdi|ssi)\w*.{0,60}(job|work|hire|employ)|(job|work|hire|employ)\w*.{0,60}(disab|ssdi|ssi)", re.I)


def sc_key():
    for line in ENV.read_text().splitlines():
        if line.startswith("SCRAPECREATORS_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("SCRAPECREATORS_API_KEY not found in last30days .env")


def get(path, **params):
    url = f"{BASE}/{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"x-api-key": KEY})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def score(title):
    if CORE.search(title):
        return 10
    if PROGRAM.search(title):
        return 8
    if IMPLIED.search(title):
        return 6
    return 0


KEY = sc_key()
videos = {}
for q in QUERIES:
    try:
        data = get("search", query=q)
        vids = data.get("videos") or []
    except Exception as e:
        print(f"  FAIL {q}: {type(e).__name__}", flush=True)
        continue
    fresh = 0
    for v in vids:
        vid = v.get("id")
        s = score(v.get("title") or "")
        if not vid or s == 0:
            continue
        if vid in videos:
            continue
        ch = v.get("channel") or {}
        videos[vid] = {
            "video_url": v.get("url") or f"https://www.youtube.com/watch?v={vid}",
            "title": (v.get("title") or "").strip(),
            "channel": ch.get("title") or "",
            "channel_handle": ch.get("handle") or "",
            "views": v.get("viewCountInt") or 0,
            "published": (v.get("publishedTime") or "")[:10],
            "score": s,
            "found_via": q,
        }
        fresh += 1
    print(f"  {q}: {len(vids)} videos, {fresh} new signal videos", flush=True)
    time.sleep(0.6)

# channel density
chan = {}
for v in videos.values():
    c = chan.setdefault(v["channel"], {"videos": 0, "views": 0, "handle": v["channel_handle"], "best": 0})
    c["videos"] += 1
    c["views"] += v["views"]
    c["best"] = max(c["best"], v["score"])

# comments pass on top videos: score desc, views desc, cap 10
top = sorted(videos.values(), key=lambda v: (-v["score"], -v["views"]))[:10]
print(f"\ncomments pass on top {len(top)} videos...", flush=True)
for v in top:
    try:
        data = get("video/comments", url=v["video_url"])
        comments = data.get("comments") or data.get("data") or []
        qs = []
        for c in comments[:40]:
            text = (c.get("content") or c.get("text") or c.get("comment") or "").strip().replace("\n", " ")
            if "?" in text and 15 < len(text) < 220:
                qs.append(text)
        v["common_questions"] = " || ".join(qs[:3])
    except Exception as e:
        v["common_questions"] = ""
    time.sleep(0.6)

rows = sorted(videos.values(), key=lambda v: (-v["score"], -v["views"]))
for r in rows:
    c = chan[r["channel"]]
    r["partnership_score"] = 9 if c["videos"] >= 2 else (8 if r["score"] >= 8 and r["views"] >= 10000 else 6)
    r["contact_path"] = f"https://www.youtube.com/@{r['channel_handle']}/about" if r["channel_handle"] else ""
    r["action"] = "partner" if r["partnership_score"] >= 8 else "monitor"
    r.setdefault("common_questions", "")

out = WORKDIR / "track2_youtube.csv"
cols = ["channel", "channel_handle", "video_url", "title", "views", "published",
        "score", "partnership_score", "action", "common_questions", "contact_path", "found_via"]
with out.open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)

print(f"\nwrote {len(rows)} signal videos -> {out}")
print("\nchannel density (videos / total views / best score):")
for name, c in sorted(chan.items(), key=lambda x: (-x[1]["videos"], -x[1]["views"]))[:12]:
    print(f"  {name} (@{c['handle']}): {c['videos']} / {c['views']:,} / {c['best']}")
