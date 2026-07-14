#!/usr/bin/env python3
"""Build the browsable "book" (index.html) from an ALLSUP leads CSV.

Usage: python3 build_book.py <leads.csv> <out_dir>
Writes <out_dir>/index.html — a self-contained, themeable, searchable, tier-filterable
page. CSV columns expected: tier,handle,source,quote,source_post,reachable_profile.
"""
import csv, json, os, sys, datetime

TEMPLATE = r"""<title>Allsup SSDI Leads — __DATE_ISO__</title>
<style>
  :root {
    --paper:#f4f2ee; --card:#fbfaf8; --ink:#1b1f23; --muted:#5c636c; --faint:#8b9199;
    --line:#e2ddd4; --accent:#2f6f6a; --best:#b4530a; --better:#2f6f6a; --good:#6b7280;
    --best-wash:#f6ead9; --better-wash:#dfeceb; --good-wash:#e7e9ec;
    --shadow:0 1px 2px rgba(27,31,35,.05),0 4px 14px rgba(27,31,35,.05);
  }
  @media (prefers-color-scheme:dark){:root{
    --paper:#131619; --card:#1b1f23; --ink:#e7e9eb; --muted:#9aa1a9; --faint:#6b727a;
    --line:#2a2f35; --accent:#4fb3ab; --best:#e08a3c; --better:#4fb3ab; --good:#99a1ac;
    --best-wash:#2c2016; --better-wash:#14251f; --good-wash:#21262c;
    --shadow:0 1px 2px rgba(0,0,0,.3),0 6px 18px rgba(0,0,0,.28);}}
  :root[data-theme="light"]{--paper:#f4f2ee;--card:#fbfaf8;--ink:#1b1f23;--muted:#5c636c;--faint:#8b9199;--line:#e2ddd4;--accent:#2f6f6a;--best:#b4530a;--better:#2f6f6a;--good:#6b7280;--best-wash:#f6ead9;--better-wash:#dfeceb;--good-wash:#e7e9ec;--shadow:0 1px 2px rgba(27,31,35,.05),0 4px 14px rgba(27,31,35,.05);}
  :root[data-theme="dark"]{--paper:#131619;--card:#1b1f23;--ink:#e7e9eb;--muted:#9aa1a9;--faint:#6b727a;--line:#2a2f35;--accent:#4fb3ab;--best:#e08a3c;--better:#4fb3ab;--good:#99a1ac;--best-wash:#2c2016;--better-wash:#14251f;--good-wash:#21262c;--shadow:0 1px 2px rgba(0,0,0,.3),0 6px 18px rgba(0,0,0,.28);}
  *{box-sizing:border-box;}
  body{margin:0;background:var(--paper);color:var(--ink);font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;line-height:1.5;-webkit-font-smoothing:antialiased;}
  .wrap{max-width:760px;margin:0 auto;padding:0 18px 80px;}
  header.masthead{padding:34px 0 22px;border-bottom:1px solid var(--line);}
  .eyebrow{font-size:12px;letter-spacing:.16em;text-transform:uppercase;color:var(--faint);font-weight:600;margin:0 0 10px;}
  h1{font-size:30px;line-height:1.12;margin:0;font-weight:700;letter-spacing:-.015em;text-wrap:balance;}
  .sub{color:var(--muted);font-size:15px;margin:10px 0 0;max-width:60ch;}
  .sub b{color:var(--ink);font-weight:600;}
  .controls{position:sticky;top:0;z-index:5;background:color-mix(in srgb,var(--paper) 88%,transparent);backdrop-filter:blur(8px);border-bottom:1px solid var(--line);padding:12px 0;margin-bottom:8px;}
  .controls-inner{display:flex;flex-wrap:wrap;gap:10px;align-items:center;}
  .search{flex:1 1 200px;display:flex;align-items:center;gap:8px;background:var(--card);border:1px solid var(--line);border-radius:9px;padding:8px 11px;color:var(--muted);}
  .search input{border:0;background:transparent;color:var(--ink);font-size:14px;width:100%;outline:none;font-family:inherit;}
  .chips{display:flex;gap:6px;}
  .chip{font:inherit;font-size:13px;font-weight:600;padding:7px 13px;border-radius:999px;cursor:pointer;border:1px solid var(--line);background:var(--card);color:var(--muted);display:inline-flex;align-items:center;gap:7px;transition:background .12s,color .12s,border-color .12s;}
  .chip .n{font-variant-numeric:tabular-nums;color:var(--faint);font-weight:700;}
  .chip[aria-pressed="true"]{background:var(--ink);color:var(--paper);border-color:var(--ink);}
  .chip[aria-pressed="true"] .n{color:var(--paper);}
  .chip:focus-visible{outline:2px solid var(--accent);outline-offset:2px;}
  .dot{width:8px;height:8px;border-radius:50%;}
  .dot.best{background:var(--best);}.dot.better{background:var(--better);}.dot.good{background:var(--good);}
  .tier-head{display:flex;align-items:baseline;gap:10px;margin:30px 0 12px;padding-bottom:6px;}
  .tier-head h2{font-size:13px;letter-spacing:.14em;text-transform:uppercase;margin:0;font-weight:700;}
  .tier-head .count{font-size:13px;color:var(--faint);font-variant-numeric:tabular-nums;}
  .tier-head .desc{font-size:13px;color:var(--muted);margin-left:auto;text-align:right;}
  h2.best{color:var(--best);}h2.better{color:var(--better);}h2.good{color:var(--good);}
  .cards{display:flex;flex-direction:column;gap:12px;}
  .card{background:var(--card);border:1px solid var(--line);border-radius:12px;box-shadow:var(--shadow);padding:16px 18px 14px 20px;position:relative;overflow:hidden;}
  .card::before{content:"";position:absolute;left:0;top:0;bottom:0;width:4px;}
  .card.best::before{background:var(--best);}.card.better::before{background:var(--better);}.card.good::before{background:var(--good);}
  blockquote{margin:0 0 14px;font-family:Georgia,"Times New Roman",serif;font-size:16.5px;line-height:1.55;color:var(--ink);}
  blockquote .more{color:var(--faint);font-family:ui-sans-serif,system-ui,sans-serif;font-size:12.5px;}
  .meta{display:flex;flex-wrap:wrap;align-items:center;gap:8px 12px;}
  .handle{font-family:ui-monospace,"SF Mono",Menlo,Consolas,monospace;font-size:13px;color:var(--muted);font-weight:500;}
  .src{font-size:11px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;padding:2px 7px;border-radius:5px;}
  .src.reddit{background:var(--best-wash);color:var(--best);}.src.x{background:var(--good-wash);color:var(--ink);}
  .links{margin-left:auto;display:flex;gap:8px;}
  a.link{font-size:12.5px;font-weight:600;color:var(--accent);text-decoration:none;border:1px solid color-mix(in srgb,var(--accent) 35%,var(--line));padding:5px 10px;border-radius:7px;white-space:nowrap;transition:background .12s;}
  a.link:hover{background:color-mix(in srgb,var(--accent) 12%,transparent);}
  a.link:focus-visible{outline:2px solid var(--accent);outline-offset:2px;}
  a.link.primary{background:var(--accent);color:var(--card);border-color:var(--accent);}
  a.link.primary:hover{filter:brightness(1.08);}
  .empty{color:var(--muted);text-align:center;padding:50px 0;font-size:15px;}
  footer{margin-top:40px;padding-top:18px;border-top:1px solid var(--line);color:var(--faint);font-size:12.5px;line-height:1.6;}
  .theme-toggle{background:var(--card);border:1px solid var(--line);color:var(--muted);border-radius:8px;padding:7px 10px;cursor:pointer;font:inherit;font-size:13px;}
  .theme-toggle:focus-visible{outline:2px solid var(--accent);outline-offset:2px;}
</style>
<div class="wrap">
  <header class="masthead">
    <p class="eyebrow">Allsup · SSDI/SSI claimant signal</p>
    <h1>Active claimant leads — __DATE_HUMAN__</h1>
    <p class="sub"><b>__TOTAL__ reachable claimants</b> pulled fresh from Reddit &amp; X over the last 30 days, tiered by claim urgency. Each is a real person, in their own words, with a public profile Allsup can reach. <b>Signal only — we never contact anyone.</b></p>
  </header>
  <div class="controls">
    <div class="controls-inner">
      <label class="search">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/></svg>
        <input id="q" type="search" placeholder="Search quotes, handles, subreddits…" aria-label="Search leads">
      </label>
      <div class="chips" role="group" aria-label="Filter by tier">
        <button class="chip" data-tier="all" aria-pressed="true">All <span class="n">__TOTAL__</span></button>
        <button class="chip" data-tier="best" aria-pressed="false"><span class="dot best"></span>Best <span class="n">__BEST__</span></button>
        <button class="chip" data-tier="better" aria-pressed="false"><span class="dot better"></span>Better <span class="n">__BETTER__</span></button>
        <button class="chip" data-tier="good" aria-pressed="false"><span class="dot good"></span>Good <span class="n">__GOOD__</span></button>
      </div>
      <button class="theme-toggle" id="themeBtn" aria-label="Toggle theme">◐</button>
    </div>
  </div>
  <main id="list" aria-live="polite"></main>
  <footer>
    Tiers — <b>Best:</b> denied / appeal / reconsideration / hearing / overpayment / can't work.
    <b>Better:</b> applying / pending / waiting / nervous.
    <b>Good:</b> work-incentive / Ticket-to-Work / benefit-impact questions.<br>
    __TOTAL__ tiered claimants · reachability-graded, no scraping · generated __DATE_ISO__.
  </footer>
</div>
<script id="data" type="application/json">__DATA__</script>
<script>
  const TIERS={best:"Best",better:"Better",good:"Good"};
  const DESC={best:"denied · appeal · hearing · overpayment",better:"applying · pending · waiting · nervous",good:"work-incentive · Ticket-to-Work"};
  const raw=JSON.parse(document.getElementById("data").textContent);
  function clean(s){if(!s)return"";s=s.replace(/submitted by[\s\S]*$/i,"");s=s.replace(/<!--[\s\S]*?-->/g," ");s=s.replace(/<[^>]*>/g," ");s=s.replace(/&amp;/g,"&").replace(/&lt;/g,"<").replace(/&gt;/g,">").replace(/&#39;|&rsquo;/g,"’").replace(/&quot;/g,'"').replace(/&nbsp;/g," ");return s.replace(/\s+/g," ").trim();}
  const leads=raw.map(l=>({...l,q:clean(l.quote)}));
  const list=document.getElementById("list"),qInput=document.getElementById("q");
  let activeTier="all",query="";
  function esc(s){return s.replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));}
  function cardHTML(l){const full=l.q;const short=full.length>240?full.slice(0,240).replace(/\s+\S*$/,""):full;const truncated=full.length>short.length;const body=truncated?`${esc(short)}… <span class="more">(${full.length} chars — open source)</span>`:esc(full);const sc=l.source==="x"?"x":"reddit";const sl=l.source==="x"?"X":"Reddit";return `<article class="card ${l.tier}"><blockquote>${body}</blockquote><div class="meta"><span class="handle">${esc(l.handle)}</span><span class="src ${sc}">${sl}</span><span class="links"><a class="link" href="${esc(l.source_post)}" target="_blank" rel="noopener">Post</a><a class="link primary" href="${esc(l.reachable_profile)}" target="_blank" rel="noopener">Profile</a></span></div></article>`;}
  function render(){const order=["best","better","good"];let html="",shown=0;for(const t of order){if(activeTier!=="all"&&activeTier!==t)continue;let group=leads.filter(l=>l.tier===t);if(query)group=group.filter(l=>(l.q+" "+l.handle+" "+l.source_post).toLowerCase().includes(query));if(!group.length)continue;shown+=group.length;html+=`<div class="tier-head"><h2 class="${t}">${TIERS[t]}</h2><span class="count">${group.length}</span><span class="desc">${DESC[t]}</span></div><div class="cards">${group.map(cardHTML).join("")}</div>`;}list.innerHTML=shown?html:`<p class="empty">No leads match “${esc(query)}”.</p>`;}
  document.querySelectorAll(".chip").forEach(btn=>{btn.addEventListener("click",()=>{activeTier=btn.dataset.tier;document.querySelectorAll(".chip").forEach(b=>b.setAttribute("aria-pressed",b===btn));render();});});
  qInput.addEventListener("input",e=>{query=e.target.value.trim().toLowerCase();render();});
  const root=document.documentElement,tb=document.getElementById("themeBtn");
  tb.addEventListener("click",()=>{const cur=root.getAttribute("data-theme")||(matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light");root.setAttribute("data-theme",cur==="dark"?"light":"dark");});
  render();
</script>
"""

def main():
    if len(sys.argv) < 3:
        sys.exit("usage: build_book.py <leads.csv> <out_dir>")
    csv_path, out_dir = sys.argv[1], sys.argv[2]
    rows = []
    with open(csv_path, newline="") as f:
        for x in csv.DictReader(f):
            rows.append({k: (x.get(k) or "").strip()
                         for k in ["tier", "handle", "source", "quote", "source_post", "reachable_profile"]})
    counts = {"best": 0, "better": 0, "good": 0}
    for r in rows:
        if r["tier"] in counts:
            counts[r["tier"]] += 1
    # date from filename (ALLSUP-LEADS-YYYY-MM-DD.csv) or today
    base = os.path.basename(csv_path)
    iso = "".join(c for c in base if c.isdigit() or c == "-")
    try:
        d = datetime.date.fromisoformat(base.rsplit("-", 3)[-3] + "-" + base.rsplit("-", 3)[-2] + "-" + base.rsplit("-", 3)[-1].split(".")[0])
    except Exception:
        d = datetime.date.today()
    human = d.strftime("%B %-d, %Y") if hasattr(d, "strftime") else str(d)
    # Quotes are untrusted public post text. Neutralize <script> break-out and JS line
    # terminators before embedding the JSON inside a <script> tag (XSS-safe).
    safe_data = (json.dumps(rows)
                 .replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
                 .replace(" ", "\\u2028").replace(" ", "\\u2029"))
    html = (TEMPLATE
            .replace("__DATA__", safe_data)
            .replace("__DATE_ISO__", d.isoformat())
            .replace("__DATE_HUMAN__", human)
            .replace("__TOTAL__", str(len(rows)))
            .replace("__BEST__", str(counts["best"]))
            .replace("__BETTER__", str(counts["better"]))
            .replace("__GOOD__", str(counts["good"])))
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "index.html")
    with open(out, "w") as f:
        f.write(html)
    print(f"book: {out}  ({len(rows)} leads — best={counts['best']} better={counts['better']} good={counts['good']})")

if __name__ == "__main__":
    main()
