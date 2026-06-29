#!/usr/bin/env python3
"""Track 5 enrichment — crawl outreach-tier org websites (score >= 8) for
the safest contact path: contact page URL, emails on site, contact form.

Uses Scrapling Fetcher (fast mode, TLS impersonation) — same engine as
scrapling-cli. Writes outreach_ready.csv and enrich_log.jsonl (resumable).
"""
import csv
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urljoin, urlparse

from scrapling.fetchers import Fetcher

HERE = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else Path.home() / "Desktop/signal-mine"
LOG = HERE / "enrich_log.jsonl"
TIMEOUT = 20
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
SKIP_EMAIL = re.compile(r"\.(png|jpg|jpeg|gif|svg|webp)$|example\.|sentry|wixpress|@2x", re.I)
CONTACT_WORDS = ("contact", "about", "get-in-touch", "connect", "staff", "team", "reach-us")


def fetch(url):
    return Fetcher.get(url, timeout=TIMEOUT, follow_redirects=True, stealthy_headers=True)


def extract_emails(page):
    found = set()
    for m in EMAIL_RE.findall(page.html_content or ""):
        if not SKIP_EMAIL.search(m):
            found.add(m.lower())
    return sorted(found)[:5]


def find_contact_link(page, base_url):
    best = None
    for a in page.css("a"):
        href = a.attrib.get("href") or ""
        text = (a.text or "").lower()
        hl = href.lower()
        if any(w in hl or w in text for w in CONTACT_WORDS):
            absolute = urljoin(base_url, href)
            if urlparse(absolute).netloc == urlparse(base_url).netloc:
                # prefer explicit "contact" over "about"
                if "contact" in hl or "contact" in text:
                    return absolute
                best = best or absolute
    return best


def has_form(page):
    return bool(page.css("form input[type=email], form textarea, form input[name*=email]"))


def enrich(row):
    url = row["url"]
    result = {"organization": row["organization"], "status": "ok",
              "contact_page": "", "emails_on_site": "", "has_contact_form": "no"}
    if not url:
        result["status"] = "no-website"
        return result
    if not url.startswith("http"):
        url = "http://" + url
    try:
        home = fetch(url)
        if home.status >= 400:
            result["status"] = f"http-{home.status}"
            return result
        emails = set(extract_emails(home))
        form = has_form(home)
        contact_url = find_contact_link(home, str(home.url) or url)
        if contact_url:
            try:
                cp = fetch(contact_url)
                if cp.status < 400:
                    result["contact_page"] = contact_url
                    emails.update(extract_emails(cp))
                    form = form or has_form(cp)
            except Exception:
                result["contact_page"] = contact_url  # link found, fetch failed
        result["emails_on_site"] = ";".join(sorted(emails)[:5])
        result["has_contact_form"] = "yes" if form else "no"
    except Exception as e:
        result["status"] = f"error: {type(e).__name__}"
    return result


def main():
    rows = [r for r in csv.DictReader(open(HERE / "org_rows.csv"))
            if int(r["score"]) >= 8]
    done = set()
    if LOG.exists():
        for line in LOG.read_text().splitlines():
            try:
                done.add(json.loads(line)["organization"])
            except Exception:
                pass
    todo = [r for r in rows if r["organization"] not in done]
    print(f"{len(rows)} targets, {len(done)} already done, {len(todo)} to crawl", flush=True)

    with LOG.open("a") as logf, ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(enrich, r): r for r in todo}
        for i, fut in enumerate(as_completed(futures), 1):
            res = fut.result()
            logf.write(json.dumps(res) + "\n")
            logf.flush()
            if i % 20 == 0:
                print(f"  {i}/{len(todo)} crawled", flush=True)

    # merge log into outreach_ready.csv
    enriched = {}
    for line in LOG.read_text().splitlines():
        try:
            e = json.loads(line)
            enriched[e["organization"]] = e
        except Exception:
            pass
    out_rows = []
    for r in rows:
        e = enriched.get(r["organization"], {})
        r = dict(r)
        r["crawl_status"] = e.get("status", "missing")
        r["contact_page"] = e.get("contact_page", "")
        r["emails_on_site"] = e.get("emails_on_site", "")
        r["has_contact_form"] = e.get("has_contact_form", "")
        # safest contact path, recomputed with crawl data
        if r["email"]:
            r["best_contact_path"] = f"direct email: {r['email']}"
        elif r["emails_on_site"]:
            r["best_contact_path"] = f"site email: {r['emails_on_site'].split(';')[0]}"
        elif r["has_contact_form"] == "yes":
            r["best_contact_path"] = f"contact form: {r['contact_page'] or r['url']}"
        elif r["phone"]:
            r["best_contact_path"] = f"phone: {r['phone']}"
        else:
            r["best_contact_path"] = "none found"
        out_rows.append(r)
    out_rows.sort(key=lambda x: (-int(x["score"]), x["organization"]))
    out = HERE / "outreach_ready.csv"
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        w.writeheader()
        w.writerows(out_rows)
    ok = sum(1 for r in out_rows if r["crawl_status"] == "ok")
    print(f"wrote {len(out_rows)} rows -> {out} (crawl ok: {ok})", flush=True)
    paths = {}
    for r in out_rows:
        k = r["best_contact_path"].split(":")[0]
        paths[k] = paths.get(k, 0) + 1
    print("contact paths:", paths, flush=True)


if __name__ == "__main__":
    main()
