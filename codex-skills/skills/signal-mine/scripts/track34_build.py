#!/usr/bin/env python3
"""Tracks 3+4 — Facebook group + Quora/forum rows from WebSearch discovery
(2026-06-10 run, SSDI/SSI work-fear vertical). Optionally enriches top Quora
questions with approximate answer-block counts via scrapling stealth.

Usage: track34_build.py [workdir] [--enrich-quora N]
"""
import csv
import re
import sys
from pathlib import Path

WORKDIR = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else Path.home() / "Desktop/signal-mine"
ENRICH_N = 5 if "--enrich-quora" in sys.argv else 0

FB_GROUPS = [
    # (url, name, signal_posts_found, evidence, score)
    ("https://www.facebook.com/groups/1708076569486771/", "(name walled — 4 benefit-fear posts found)", 4,
     "Does everyone on ssdi qualify for ticket to work; How does ticket to work affect disability benefits; SSDI application questions x2", 10),
    ("https://www.facebook.com/groups/369335143952969/", "SSI and SSDI Support Group", 2,
     "dedicated SSI/SSDI support community, surfaced in 2 separate searches", 8),
    ("https://www.facebook.com/groups/508399106244039/", "Social Security Disability Support Group", 1,
     "dedicated SSD support community", 8),
    ("https://www.facebook.com/groups/ssdi.info/", "SSDI Info", 1, "named SSDI info group", 8),
    ("https://www.facebook.com/groups/1351911332368766/", "(name walled)", 1,
     "Does ticket to work program affect ssdi eligibility?", 8),
    ("https://www.facebook.com/groups/medicaidsaveslives/", "Medicaid Saves Lives", 2,
     "SSI stopped due to DAC; disabled child SSI questions — Medicaid-loss fear adjacent", 6),
    ("https://www.facebook.com/groups/305850096291755/", "Netspend Social Security/Disability/VA", 1,
     "financial-adjacent SSI/SSDI community", 6),
    ("https://www.facebook.com/groups/1618673784950818/", "Chime SSI/SSDI/VA benefits", 1,
     "financial-adjacent benefits community", 6),
    ("https://www.facebook.com/groups/autismparenting/", "Autism Parents Support Group", 2,
     "SSI denial threads — parents-of-disabled segment", 6),
]

QUORA = [
    ("https://www.quora.com/Why-should-one-risks-losing-their-SSDI-benefits-if-they-use-SSA-Ticket-to-Work-trial-work-period-and-they-become-disabled-again-when-it-probably-took-several-years-to-be-approved-the-first-time",
     "Why risk losing SSDI via Ticket to Work when approval took years?", 10,
     "THE core fear verbatim: program participation itself seen as a risk"),
    ("https://www.quora.com/Can-I-work-as-many-hours-as-I-choose-and-still-keep-my-Social-Security-disability-benefits",
     "Can I work as many hours as I choose and keep SSDI?", 10, "hours-vs-benefits confusion"),
    ("https://www.quora.com/Would-I-still-be-able-to-work-part-time-on-disability",
     "Would I still be able to work part-time on disability?", 10, "part-time fear"),
    ("https://www.quora.com/Is-it-possible-to-work-part-time-while-receiving-Social-Security-disability-benefits-if-your-condition-allows-it",
     "Possible to work part-time while receiving SSD benefits?", 10, "part-time fear"),
    ("https://www.quora.com/Can-somebody-collect-disability-and-still-work",
     "Can somebody collect disability and still work?", 10, "core question"),
    ("https://www.quora.com/Can-you-work-while-collecting-social-security-disability",
     "Can you work while collecting social security disability?", 10, "core question"),
    ("https://www.quora.com/Is-it-possible-to-work-while-you-are-still-receiving-SSDI",
     "Is it possible to work while still receiving SSDI?", 10, "core question"),
    ("https://www.quora.com/Can-someone-who-collects-Social-Security-Disability-insurance-SSDI-work-part-time-without-losing-any-benefits-If-so-how-does-one-go-about-doing-this-legally-or-at-least-not-getting-caught-by-officials",
     "Work part-time on SSDI without losing benefits... without getting caught?", 10,
     "fear so strong it reads as evasion — confusion about legality"),
    ("https://www.quora.com/Is-it-possible-to-work-while-receiving-Social-Security-Disability-insurance-SSDI-payments-If-so-what-is-the-maximum-number-of-hours-allowed-per-week-before-benefits-are-suspended-or-terminated",
     "Max hours per week before SSDI suspended or terminated?", 10, "threshold confusion"),
    ("https://www.quora.com/If-you-are-on-SSDI-how-much-can-you-be-allowed-to-make-at-a-part-time-job",
     "How much can you make at a part-time job on SSDI?", 10, "earnings-limit confusion"),
    ("https://www.quora.com/If-while-receiving-SSDI-I-work-for-my-dad-for-a-short-time-making-less-than-800-a-month-will-I-lose-the-opportunity-to-get-training-for-a-job-I-can-do-permanently-through-the-Ticket-to-Work-program",
     "Will short-term work cost me Ticket to Work training eligibility?", 10, "program-rules fear"),
    ("https://www.quora.com/If-you-were-on-SSDI-used-your-trial-work-period-etc-then-went-back-on-SSDI-then-went-back-to-work-again-long-enough-to-lose-benefits-does-your-period-of-extended-eligibility-start-from-the-first-time-you-went-off-or",
     "EPE restart rules after second return to work?", 8, "TWP/EPE mechanics confusion"),
    ("https://www.quora.com/Can-someone-work-full-time-while-applying-for-disability",
     "Work full time while applying for disability?", 8, "application-stage fear"),
    ("https://www.quora.com/Can-I-work-part-time-while-applying-for-SSDI-disability-benefits",
     "Work part-time while applying for SSDI?", 8, "application-stage fear"),
    ("https://www.quora.com/Can-you-still-file-for-unemployment-if-you-ve-been-working-part-time-with-SSDI",
     "Unemployment + part-time SSDI interaction?", 8, "benefit-stacking confusion"),
    ("https://www.quora.com/How-can-I-get-a-SSDI-overpayment-waived",
     "How to get an SSDI overpayment waived?", 8, "overpayment fear"),
    ("https://www.quora.com/I-just-learned-that-SSDI-overpayments-are-allowed-to-be-discharged-in-bankruptcy-However-I-have-applied-again-for-disability-Does-anyone-know-how-this-would-work",
     "SSDI overpayment bankruptcy discharge + reapplication?", 8, "overpayment aftermath"),
]


def quora_answer_blocks(url):
    from scrapling.fetchers import StealthyFetcher
    p = StealthyFetcher.fetch(url, headless=True, network_idle=True, timeout=60000)
    html = p.html_content or ""
    return len(re.findall(r"q-box qu-userSelect--text", html))


def main():
    fb_out = WORKDIR / "track3_facebook.csv"
    with fb_out.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["group_url", "group_name", "signal_posts_found", "evidence",
                    "members", "public_private", "admin_contact_path", "score", "action"])
        for url, name, n, ev, s in FB_GROUPS:
            w.writerow([url, name, n, ev, "MANUAL (login-walled)", "MANUAL",
                        "join group as human, then admin DM", s,
                        "manual-review" if s >= 8 else "monitor"])
    print(f"wrote {len(FB_GROUPS)} groups -> {fb_out}")

    rows = []
    for url, worry, s, note in QUORA:
        rows.append({"question_url": url, "exact_worry": worry, "score": s, "note": note,
                     "answers_approx": "", "action": "place-content" if s == 10 else "monitor"})
    if ENRICH_N:
        print(f"answer-count pass on top {ENRICH_N} Quora questions...", flush=True)
        for r in rows[:ENRICH_N]:
            try:
                r["answers_approx"] = quora_answer_blocks(r["question_url"])
                print(f"  {r['answers_approx']} blocks | {r['exact_worry'][:60]}", flush=True)
            except Exception as e:
                print(f"  FAIL {type(e).__name__} | {r['exact_worry'][:60]}", flush=True)

    q_out = WORKDIR / "track4_quora.csv"
    with q_out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} questions -> {q_out}")


if __name__ == "__main__":
    main()
