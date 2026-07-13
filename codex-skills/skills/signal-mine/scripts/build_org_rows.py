#!/usr/bin/env python3
"""Track 5 (provider/source nodes) — normalize SSA Choose Work directory
pulls into scored signal-mine rows.

Input:  providers_*.json (raw API pulls from choosework.ssa.gov/findhelp)
Output: org_rows.csv — one row per org, scored for partnership fit.

Partnership score rubric (org track):
  9 = WIPA — entire mandate is work-incentives counseling; their audience IS
      "afraid to work" people
  8 = EN, national/virtual (nationalStatus A) — Ticket to Work delivery orgs
  6 = EN/WF, local only
  5 = PAAP — protection & advocacy; content-placement + referral path
  4 = VR state agency — government, slow partnership path
"""
import csv
import json
import sys
from pathlib import Path

HERE = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else Path.home() / "Desktop/signal-mine"

FILES = {
    "providers_en_wf.json": "EN",
    "providers_vra.json": "VR",
    "providers_wipa.json": "WIPA",
    "providers_paap.json": "PAAP",
}


def score(restype: str, p: dict) -> int:
    if restype == "WIPA":
        return 9
    if restype == "EN":
        return 8 if p.get("nationalStatus") == "A" else 6
    if restype == "PAAP":
        return 5
    return 4  # VR


def contact_path(p: dict) -> str:
    parts = []
    if p.get("email"):
        parts.append("email")
    if p.get("phone") or p.get("tollfreeNumber") or p.get("mainPhoneNumber"):
        parts.append("phone")
    if p.get("website"):
        parts.append("website")
    return "+".join(parts) if parts else "none"


def action(s: int) -> str:
    if s >= 8:
        return "outreach"
    if s >= 5:
        return "monitor"
    return "ignore"


rows = []
for fname, restype in FILES.items():
    data = json.loads((HERE / fname).read_text())
    for p in data.get("resourceVoList") or []:
        # the en,wf pull mixes EN and WF resTypes; trust the record's own type
        rectype = (p.get("resType") or restype).upper()
        if rectype not in ("EN", "WF", "VR", "WIPA", "PAAP", "VRA"):
            rectype = restype
        if rectype == "VRA":
            rectype = "VR"
        s = score(rectype if rectype != "WF" else "EN", p)
        rows.append({
            "organization": (p.get("organizationname") or p.get("resName") or "").strip(),
            "org_type": rectype,
            "url": (p.get("website") or "").strip(),
            "contact_name": (p.get("contact") or "").strip(),
            "email": (p.get("email") or "").strip().lower(),
            "phone": (p.get("phone") or p.get("tollfreeNumber") or p.get("mainPhoneNumber") or "").strip(),
            "city": (p.get("actualCity") or "").strip(),
            "state": (p.get("actualState") or "").strip(),
            "national": "yes" if p.get("nationalStatus") == "A" else "no",
            "mentions_ticket_to_work": "yes",  # listed in the SSA TtW directory by definition
            "contact_path": contact_path(p),
            "source_url": "https://choosework.ssa.gov/findhelp/result?option=2&resStr="
                          + {"EN": "en,wf", "WF": "en,wf", "VR": "vra",
                             "WIPA": "wipa", "PAAP": "paap"}[rectype],
            "indv_id": p.get("indvId") or "",
            "score": s,
            "action": action(s),
        })

# dedupe on (organization, state) keeping highest score
seen = {}
for r in rows:
    k = (r["organization"].lower(), r["state"])
    if k not in seen or r["score"] > seen[k]["score"]:
        seen[k] = r
rows = sorted(seen.values(), key=lambda r: (-r["score"], r["organization"]))

out = HERE / "org_rows.csv"
with out.open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

by_type = {}
by_action = {}
for r in rows:
    by_type[r["org_type"]] = by_type.get(r["org_type"], 0) + 1
    by_action[r["action"]] = by_action.get(r["action"], 0) + 1
print(f"wrote {len(rows)} rows -> {out}")
print("by type:", by_type)
print("by action:", by_action)
print("rows with email:", sum(1 for r in rows if r["email"]))
print("rows with website:", sum(1 for r in rows if r["url"]))
