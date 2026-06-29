#!/usr/bin/env python3
"""Refine pipeline helper: ore -> Sherlock-confirm -> split -> blue-healer resolve.

Deterministic glue for the /refine skill. Never prints secret values.

Subcommands:
  envcheck                         load keys, live-test Oxylabs auth (names only)
  usernames  <ore.jsonl>           extract clean usernames -> <out>/usernames.txt
  classify   <ore.jsonl> <sher_dir>  score Sherlock CSVs, split orgs/individuals
  resolve    <bh_dir> <users.txt>   drive blue-healer, write contact_cards.json
"""
import argparse, csv, glob, json, os, re, sys, time, base64, ssl, subprocess, urllib.request

ENV_FILES = ["~/Desktop/GitSync/kloop.env", "~/.config/last30days/.env"]
NEEDED = ["SERPER_API_KEY", "SCRAPECREATORS_API_KEY", "LINKD_API_KEY",
          "OXYLABS_USERNAME", "OXYLABS_PASSWORD"]
ORG_KW = re.compile(
    r'law|legal|firm|group|attorney|advoc|benefit|disabilit|gov|planning|service|'
    r'agency|academy|official|insur|claim|expert|consult|coach|institute|center|'
    r'associat|\.com$|llc|inc|nutrition|finance', re.I)


def load_env():
    """Parse only well-formed KEY=VALUE lines (kloop.env has prose — not sourceable)."""
    env = {}
    for path in ENV_FILES:
        try:
            lines = open(os.path.expanduser(path)).read().splitlines()
        except FileNotFoundError:
            continue
        for ln in lines:
            m = re.match(r'^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)=(.*)$', ln)
            if m:
                k, v = m.group(1), m.group(2).strip().strip('"').strip("'")
                if v and k not in env:
                    env[k] = v
    return env


def cmd_envcheck(_a):
    env = load_env()
    for k in NEEDED:
        print(f"  {k}: {'PRESENT' if env.get(k) else 'MISSING'}")
    u, p = env.get("OXYLABS_USERNAME", ""), env.get("OXYLABS_PASSWORD", "")
    if "@" in u:
        print("  WARNING: OXYLABS_USERNAME looks like an email — use the Web Scraper API "
              "sub-user, not your account login (will 401).")
    if not (u and p):
        print("Oxylabs: cannot test (missing creds)"); return
    # Verified TLS — creds ride in the Authorization header, so never disable verification.
    try:
        import certifi
        ctx = ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        ctx = ssl.create_default_context()
    auth = base64.b64encode(f"{u}:{p}".encode()).decode()
    body = json.dumps({"source": "universal", "url": "https://ip.oxylabs.io/location"}).encode()
    req = urllib.request.Request("https://realtime.oxylabs.io/v1/queries", data=body,
            headers={"Authorization": f"Basic {auth}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60, context=ctx) as r:
            ok = bool(json.loads(r.read().decode()).get("results"))
            print(f"  Oxylabs auth: HTTP {r.status} -> {'OK' if ok else 'reachable, empty'}")
    except urllib.error.HTTPError as e:
        print(f"  Oxylabs auth: HTTP {e.code} -> "
              f"{'AUTH FAILED (wrong sub-user/pass)' if e.code in (401, 403) else 'error'}")
    except Exception as e:
        print(f"  Oxylabs auth: ERROR {type(e).__name__}")


def _ore_handles(ore_path):
    """Yield (source, signal, text, clean_handle) for rows that have a handle."""
    for ln in open(ore_path):
        r = json.loads(ln)
        h = (r.get("handle") or "").lstrip("@").strip()
        if h:
            yield r.get("source", ""), r.get("signal", "") or "", r.get("text", "") or "", h


def cmd_usernames(a):
    os.makedirs(a.out, exist_ok=True)
    seen, clean, dirty = set(), [], 0
    for _s, _sig, _t, h in _ore_handles(a.ore):
        if re.fullmatch(r'[A-Za-z0-9_]+', h):
            if h.lower() not in seen:
                seen.add(h.lower()); clean.append(h)
        else:
            dirty += 1
    open(os.path.join(a.out, "usernames.txt"), "w").write("\n".join(clean) + "\n")
    print(f"{len(clean)} clean usernames -> {a.out}/usernames.txt "
          f"({dirty} dotted/special handles dropped)")


def _presence_counts(sher_dir):
    counts = {}
    for f in glob.glob(os.path.join(sher_dir, "*.csv")):
        u = os.path.splitext(os.path.basename(f))[0]
        n = sum(1 for row in csv.DictReader(open(f))
                if (row.get("exists") or "").strip().lower() in ("claimed", "true", "yes"))
        counts[u] = n
    return counts


def _is_org(u, rec):
    hl, txt, sig, s = u.lower(), (rec.get("text") if rec else "") or "", \
        (rec.get("signal") if rec else "") or "", 0
    if ORG_KW.search(hl): s += 2
    if ORG_KW.search(txt[:200]): s += 1
    if re.match(r'^[A-Z][a-z]+\d', u) or re.match(r'^[a-z]+_[a-z]+$', u): s -= 1
    if sig == "fear": s -= 1
    if sig == "build": s += 1
    return s >= 2


def cmd_classify(a):
    os.makedirs(a.out, exist_ok=True)
    counts = _presence_counts(a.sher_dir)
    rec = {}
    for s, sig, t, h in _ore_handles(a.ore):
        rec.setdefault(h.lower(), {"source": s, "signal": sig, "text": t})
    confirmed = {u: n for u, n in counts.items() if n >= a.min_platforms}
    orgs = [u for u in confirmed if _is_org(u, rec.get(u.lower()))]
    indiv = [u for u in confirmed if u not in orgs]
    for name, lst in [("confirmed", sorted(confirmed, key=lambda x: -confirmed[x])),
                      ("orgs", orgs), ("individuals", indiv)]:
        open(os.path.join(a.out, f"{name}.txt"), "w").write("\n".join(lst) + "\n")
    print(f"swept: {len(counts)} | confirmed (>={a.min_platforms} platforms): {len(confirmed)}")
    print(f"  -> orgs/creators: {len(orgs)}   individuals: {len(indiv)}")
    print(f"  files in {a.out}: confirmed.txt, orgs.txt, individuals.txt")
    print("\nNOTE: individuals = the sensitive group. Show Brent the split; let him pick.")


def cmd_resolve(a):
    bh = os.path.expanduser(a.bh_dir)
    appdir = os.path.join(bh, "app")
    # 1. clean gitignored .env (only needed keys; never copy kloop.env in)
    env = load_env()
    with open(os.path.join(appdir, ".env"), "w") as f:
        for k in NEEDED:
            if env.get(k):
                f.write(f"{k}={env[k]}\n")
    os.chmod(os.path.join(appdir, ".env"), 0o600)
    # 2. launch server on a free port
    import socket
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    launcher = (f"import os,sys;os.chdir({appdir!r});sys.path.insert(0,{appdir!r});"
                f"import main;main.app.run(host='127.0.0.1',port={port},debug=False,use_reloader=False)")
    py = os.path.join(bh, ".venv", "bin", "python")
    proc = subprocess.Popen([py, "-c", launcher],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    base = f"http://127.0.0.1:{port}"
    try:
        for _ in range(30):
            try:
                urllib.request.urlopen(base + "/api/enrichment-status", timeout=3); break
            except Exception:
                time.sleep(1)
        users = [l.strip() for l in open(a.users) if l.strip()]
        if not users:
            print("no usernames to resolve"); return
        body = json.dumps({"usernames": ", ".join(users), "timeout": 8,
                           "recursive": True, "max_depth": 1, "enrich": True}).encode()
        req = urllib.request.Request(base + "/api/search", data=body,
                                     headers={"Content-Type": "application/json"})
        jid = json.loads(urllib.request.urlopen(req, timeout=30).read())["job_id"]
        print(f"job {jid} on {len(users)} usernames; polling (slow — 3k+ sites each)...")
        while True:
            j = json.loads(urllib.request.urlopen(f"{base}/api/job/{jid}", timeout=10).read())
            if j.get("status") in ("done", "error"):
                break
            print(f"  running: records={j.get('record_count')} cards={j.get('card_count')} "
                  f"errors={j.get('error_count')}", flush=True)
            time.sleep(20)
        payload = urllib.request.urlopen(f"{base}/api/job/{jid}/download/json", timeout=30).read()
        open(a.out, "wb").write(payload)
        data = json.loads(payload)
        cards = data.get("contact_cards", [])
        with_email = sum(1 for c in cards if c.get("emails") or c.get("email"))
        print(f"done: {len(cards)} contact cards ({with_email} with a candidate email) -> {a.out}")
    finally:
        proc.terminate()


def main():
    ap = argparse.ArgumentParser(description="Refine pipeline helper")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("envcheck").set_defaults(fn=cmd_envcheck)
    p = sub.add_parser("usernames"); p.add_argument("ore"); p.add_argument("--out", required=True); p.set_defaults(fn=cmd_usernames)
    p = sub.add_parser("classify"); p.add_argument("ore"); p.add_argument("sher_dir"); p.add_argument("--out", required=True); p.add_argument("--min-platforms", type=int, default=2); p.set_defaults(fn=cmd_classify)
    p = sub.add_parser("resolve"); p.add_argument("bh_dir"); p.add_argument("users"); p.add_argument("--out", required=True); p.set_defaults(fn=cmd_resolve)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
