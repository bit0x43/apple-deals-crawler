# Roadmap: apple-deals-crawler

## Milestones

- ✅ **v1.0 Core** — Phases 1-8 (shipped 2026-05-11)
- ✅ **Phase 9** — Data Quality & Bug Fixes (completed 2026-05-11)
- ✅ **Phase 10** — TUI Filters & Ordering (completed 2026-05-12)
- ✅ **v1.1 Alert Quality** — Phase 11 (shipped 2026-05-12)

<details>
<summary>✅ v1.0 Core (Phases 1-8) — SHIPPED 2026-05-11</summary>

- [x] Phase 1: Project Foundation (3/3 plans) — completed 2026-05-08
- [x] Phase 2: Crawling Core (3/3 plans) — completed 2026-05-08
- [x] Phase 3: Database & Maintenance (2/2 plans) — completed 2026-05-08
- [x] Phase 4: TUI (1 plan) — completed 2026-05-09
- [x] Phase 5: Telegram Alerts (2/2 plans) — completed 2026-05-09
- [x] Phase 6: Automation & Deployment (3/3 plans) — completed 2026-05-11
- [x] Phase 7: Documentation (1 plan) — completed 2026-05-11
- [x] Phase 8: Stock Tracking & RAM Enrichment (1 plan) — completed 2026-05-11

</details>

<details>
<summary>✅ Phase 9: Data Quality & Bug Fixes (1 plan) — completed 2026-05-11</summary>

- [x] Phase 9: Data Quality & Bug Fixes (1 plan) — Fix Shopify sentinel prices (99,999,999), DB data cleaning (22 sentinel records deleted, 61 source names normalized), plus TUI crash fixes from previous session — completed 2026-05-11

</details>

<details>
<summary>✅ Phase 10: TUI Filters & Ordering (1 plan) — completed 2026-05-12</summary>

- [x] Phase 10: TUI Filters & Ordering — Add stock (in-stock/out-of-stock), memory, and storage filter controls to the catalog view. Add column-based ordering for memory and storage columns alongside existing price ordering. Use Textual widgets with thread-worker DB queries.

</details>

<details>
<summary>✅ v1.1: Alert Quality (Phase 11) — SHIPPED 2026-05-12</summary>

- [x] Phase 11: Alert Noise Filtering — Add in_stock gating to send_alert() and send_high_memory_alert() in telegram.py to suppress false-positive alerts for out-of-stock products. 4 new tests added, 86 total tests passing.

</details>

---

*Roadmap created: 2026-05-08*
*Last updated: 2026-05-12 — Phase 10 complete, v1.1 started*
