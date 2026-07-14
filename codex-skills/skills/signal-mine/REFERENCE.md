# Signal Mine — Reference

## Definitions

- **Scrape**: collect URLs, posts, titles, comments, creators, groups, forums.
- **Mine**: extract meaning — what fear shows up, how often, on what platform,
  what exact words, one-off post vs dense community, is there a contact path,
  consumer lead vs creator lead vs partner lead.

## Data model (every mined item = one row)

| Field | Meaning |
|-------|---------|
| URL | Where the signal appeared |
| Platform | Reddit, YouTube, Facebook, Quora, forum, org site |
| Signal phrase | Exact phrase showing fear/confusion |
| Lead type | Vertical-specific categories (see vertical config) |
| Work status | wants work, working, tried work, afraid to work (vertical-specific) |
| Fear | The specific fear expressed |
| Density | How often this shows up |
| Contact path | creator, admin, org, public comment, no path |
| Score | 0-10 (rubric below) |
| Action | ignore, monitor, outreach, partner, place content |

## Signal score rubric (content tracks 1-4)

- **10** = direct statement of the vertical's core question (e.g. "Can I work
  and keep SSDI/SSI?")
- **8** = adjacent program/term signals (e.g. Ticket to Work, Trial Work
  Period, WIPA, overpayment, SGA)
- **6** = target population with implied core fear (e.g. disabled job seekers)
- **4** = general community for the vertical, no work/fear signal
- **0** = no relevant signal

## Org partnership score rubric (track 5)

- **9** = org whose entire mandate is the vertical's core fear (e.g. WIPA —
  work-incentives counseling)
- **8** = national/virtual delivery org in the program (e.g. EN with
  nationalStatus A)
- **6** = local delivery org
- **5** = advocacy/legal org (content placement + referral path)
- **4** = government agency (slow partnership path)

Action mapping: score >= 8 → outreach, 5-7 → monitor, < 5 → ignore.

## Contact-path priority (safest first)

1. Direct email published in a directory (org gave it to be contacted)
2. Email published on the org's own site
3. Contact form on the org's site
4. Phone
5. Public comment / creator About page (content tracks)
6. None found → flag, never force a path

## Proven implementation notes

- **SSA Choose Work directory JSON API** (found 2026-06-10): the magic param
  is `option=2`. `GET https://choosework.ssa.gov/findhelp/sortByName?option=2&resStr=<types>&p_pagesize=0&p_pagenum=1`
  with browser UA + `X-Requested-With: XMLHttpRequest` returns ALL providers
  as JSON (`resourceVoList`). resStr values: `en,wf` / `vra` / `wipa` / `paap`.
  Detail per org: `/findhelp/enData?indvId=<id>`. Without `option=2` you get a
  27,215-byte HTML ERROR page — that exact byte size means wrong params.
- **WIPA records have no email in the directory** — only phone/website. Site
  enrichment (crawl homepage + contact page) recovers emails for most (69/72
  on first run).
- **Scrapling install**: plain `pip install scrapling` is missing curl_cffi;
  use `pip install 'scrapling[all]'` (matches scrapling-cli requirements).
- **Reddit public search.json returns 403** from this network; RSS
  (`/search.rss`) works keyless, and ScrapeCreators has a Reddit backup.
- Brent's scrapling-cli repo: `bbrysonelite-max/scrapling-cli`, local clone at
  `~/Desktop/scrapling-cli/` — use for stealth/dynamic fetches (Quora).

## Pat-facing frame (use verbatim when summarizing)

"We are not scraping disabled people. We are signal mining public
conversations where people are afraid that working will cost them disability
benefits. The deliverable is a map of high-density communities, creators,
forums, and organizations where that fear appears repeatedly, plus the safest
contact path for each source."
