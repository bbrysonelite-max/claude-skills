#!/usr/bin/env python3
"""skill-miner digest — extract Brent's human prompts + slash-commands from Claude Code
session transcripts into a compact, analyzable digest (and optional fan-out batches).

The transcripts are huge (100MB+) JSONL; the signal for "what routines recur" is in the
HUMAN prompts. This streams each file, keeps only real human turns (not tool-results /
subagent sidechains / hook noise), truncates each, and writes one block per session.

Usage:
  python3 digest.py [--dir DIR] [--out OUT] [--batches N] [--limit N]
Defaults: DIR=~/.claude/projects/-Users-brentbryson  OUT=<cwd>/digest.txt
"""
import json, os, glob, re, sys, argparse
from collections import Counter

ap = argparse.ArgumentParser()
ap.add_argument("--dir", default=os.path.expanduser("~/.claude/projects/-Users-brentbryson"))
ap.add_argument("--out", default=os.path.join(os.getcwd(), "digest.txt"))
ap.add_argument("--batches", type=int, default=0, help="also split sessions into N batchK.txt files (next to --out)")
ap.add_argument("--limit", type=int, default=0, help="only the N most recently-modified sessions (0 = all)")
args = ap.parse_args()

files = glob.glob(os.path.join(args.dir, "*.jsonl"))
files.sort(key=lambda p: os.path.getmtime(p))  # oldest-first
if args.limit and len(files) > args.limit:
    files = files[-args.limit:]

NOISE = ("Caveat:", "This session is being continued", "<local-command",
         "[Request interrupted", "The user doesn't want to proceed")

def clean(t):
    t = re.sub(r"<system-reminder>.*?</system-reminder>", "", t, flags=re.S)
    t = re.sub(r"<command-message>.*?</command-message>", "", t, flags=re.S)
    return re.sub(r"\s+", " ", t).strip()

sessions = []
for f in files:
    sid, date, prompts, cmds = os.path.basename(f)[:8], "?", [], []
    try:
        with open(f, "r", errors="ignore") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    o = json.loads(line)
                except Exception:
                    continue
                if date == "?" and o.get("timestamp"):
                    date = o["timestamp"][:10]
                if o.get("type") != "user" or o.get("isSidechain") or o.get("isMeta"):
                    continue
                c = o.get("message", {}).get("content")
                if isinstance(c, str):
                    text = c
                elif isinstance(c, list):
                    parts = [b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text"]
                    if not parts:
                        continue  # tool_result-only — skip
                    text = " ".join(parts)
                else:
                    continue
                for m in re.findall(r"<command-name>([^<]+)</command-name>", text or ""):
                    cmds.append(m.strip())
                text = clean(text or "")
                if not text or text.startswith(NOISE):
                    continue
                prompts.append(text[:320] + ("…" if len(text) > 320 else ""))
    except Exception as e:
        prompts.append(f"[read error: {e}]")
    sessions.append((date, sid, prompts, cmds))

def render(sess):
    out = []
    for date, sid, prompts, cmds in sess:
        out.append(f"\n===== SESSION {sid}  ({date})  — {len(prompts)} human prompts =====")
        if cmds:
            out.append("slash-commands: " + ", ".join(f"/{k}×{v}" for k, v in Counter(cmds).most_common()))
        for i, p in enumerate(prompts[:50], 1):
            out.append(f"{i:>2}. {p}")
        if len(prompts) > 50:
            out.append(f"   …(+{len(prompts)-50} more prompts)")
    return "\n".join(out)

header = f"# skill-miner prompt digest — {len(sessions)} sessions"
if sessions:
    header += f" ({sessions[0][0]} .. {sessions[-1][0]})"
allc = Counter()
for *_, cmds in sessions:
    allc.update(cmds)
tally = "\n\n===== GLOBAL SLASH-COMMAND TALLY =====\n" + "\n".join(f"/{k}: {v}" for k, v in allc.most_common())

with open(args.out, "w") as fh:
    fh.write(header + "\n" + render(sessions) + tally + "\n")

if args.batches and args.batches > 1 and sessions:
    n = args.batches
    size = (len(sessions) + n - 1) // n
    base = os.path.dirname(args.out) or "."
    for b in range(n):
        chunk = sessions[b*size:(b+1)*size]
        if not chunk:
            continue
        with open(os.path.join(base, f"batch{b+1}.txt"), "w") as fh:
            fh.write(f"# batch {b+1}/{n}\n" + render(chunk) + "\n")

print(f"sessions: {len(sessions)}")
print(f"human prompts: {sum(len(p) for _, _, p, _ in sessions)}")
print(f"wrote: {args.out}" + (f"  + {args.batches} batches" if args.batches else ""))
