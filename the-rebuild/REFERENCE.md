# The Rebuild — Reference (links, assets, citations)

## Live webinar funnel ("Flip the Script", WebinarKit Pro, ACTIVE)
- **Share this only (registration):** https://webinarkit.com/webinar/registration/6a309442f81002110816b863
- Watch room: https://webinarkit.com/webinar/watch/6a309442f81002110816b863
- Replay: https://webinarkit.com/replay/6a309442f81002110816b863
- Control room — PRIVATE backstage, never share: https://webinarkit.com/webinar/control/room/6a309442f81002110816b863
- Free-call booking (Cal.com): https://cal.com/brent-bryson-l9viqn/flip-the-script
- Webinar video = built in HeyGen with Brent's clone ("Corrected Brent clone — blue polo office"; voice "Brent Bryson"). 4 min, 12 scenes. Feature scenes double as reusable shorts/cards.

## Repos / locations
- **Canonical webinar repo (private):** github.com/bbrysonelite-max/Tiger-Webinar-Funnel — local `~/Desktop/tiger-webinar-funnel` (webinar-script.md, heygen-production.md, booking-page.md, README).
- **Tiger product (canonical):** `/Users/brentbryson/tiger-claw-v4-core` (Grep/Glob/Read, never the GitHub API; `git pull` first).
- **The agnostic Mine:** `~/signal-atlas` (5 tracks proven) + `~/Datamine` (v1 + Hunter.io) — on the **iMac** `2020iMac.local` / 192.168.0.116, SSH `brentbryson` with `~/.ssh/trashcan` key. Also runnable via the local `signal-mine` skill (scripts + keys present on this machine).
- **NM vertical config:** `~/.claude/skills/signal-mine/verticals/network-marketers-ai.md` (Brent's build + fear phrases, YouTube queries, FB groups).

## Data-safety code citations (tiger-claw-v4-core)
- Durable, tenant-scoped: `migrations/006_tenant_data.sql` (`tenant_leads`, `tenant_contacts`, `tenant_nurture` keyed by `tenant_id`); `services/tenant_data.ts` (getLeads/saveLeads → Postgres UPSERT, not JSON files).
- CSV import: `tools/tiger_import.ts` (operator-only; preview + commit; ~20 column aliases for name/phone/email/oar/notes/tags).
- CSV export: `tools/tiger_export.ts` (`/export`; UTF-8 CSV w/ BOM; filter by status).
- Lifecycle: suspend/resume/archive RETAIN leads (`provisioner.ts`, `routes/admin.ts`); **terminate** = `dropTenantSchema()` `DROP SCHEMA ... CASCADE` (`services/db.ts`) = permanent delete, no auto-backup. No built-in "move leads to a new bot" — re-import via CSV.

## Related memory
- `project_tiger_webinar_gtm_loop.md` — the GTM loop + revenue anchor (overlaps this skill; this skill is the operator-facing brief).
- `signal-mine` skill — the runbook for the agnostic Mine (tracks 1–5, scoring rubric, keys).

## Mine → seats (how the map fills seats, when that phase comes)
The Mine produces a MAP (creators to partner with, groups to show up in, the language they use), NOT a cold list of people. Seats fill via: (a) partner with NM YouTube creators who have audiences; (b) show up in the FB groups; (c) match their language in copy. No member scraping, no cold blasts. The 1:1 named-leader list is a separate tool (`~/Desktop/operator-list-builder/`, LinkdAPI) — Tiger drafts personal invites, operator-approved.
