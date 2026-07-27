# Project Handoff

Use this as the compact continuation context for a new Codex chat.

## Snapshot

- Project: Oslo Stock web-app.
- Repo: `keresell-coder/oslo-market-workspace`.
- Local folder: `/Users/ke/Documents/Oslo Stock web-app`.
- Release target: **Beta v0.1.0**.
- Active direction: **Static GitHub Pages Remake**.
- Public URL: https://keresell-coder.github.io/oslo-market-workspace/
- Local URL: http://127.0.0.1:8765.

## Current State

- Local Python app still runs through `python3 app/server.py`.
- Public beta is static GitHub Pages reading committed JSON under `docs/data/`.
- Curated static inputs live under `data/*.yml`.
- Static builder: `scripts/build_static_site_data.py`.
- Static workflow: `.github/workflows/static-data.yml`.
- The public Watchlist currently has 15 rows, including `BRG.OL` / Borregaard
  ASA and `NORBT.OL` / Norbit ASA.
- Static Beta Follow-Up is complete: public checks passed and the operator
  verified the Pages app from an iPad on 19 May 2026.
- Current phase is beta usage feedback before further iteration.
- Low-risk watchlist and peer-group editing uses a standalone YAML validator,
  stricter peer-group checks, and the documented PR/static-data workflow.
- Current generated technical coverage has one explicit
  missing-from-latest-CSV row, `NORBT.OL`.
- Fundamental frameworks are deferred while the external `oslo-quant` framework
  screener receives final tweaks.

## Guardrails

- No buy/sell investment advice.
- No standalone cheap/expensive/fair/neutral labels.
- Missing values stay missing.
- Source, timestamp/freshness, confidence, limitations, and errors stay visible.
- Technical BUY/SELL labels are external screener source labels only.
- Public Pages must remain token-free and read-only.
- Do not edit Oslo Screener repos unless explicitly requested.

## Next Work

Current phase:

- Let the operator use the public beta and return with practical feedback.
- Keep Beta v0.1.0 watchlist-focused for now.
- Monitor scheduled static-data workflow behavior during normal use.
- Do not start further UX/feature tweaks until feedback arrives.

Implemented edit workflow:

- Use YAML plus `scripts/validate_static_inputs.py` plus static data generation
  as the default safe edit path.
- Watchlist edits go through `data/watchlist.yml`.
- Peer-group edits go through `data/peer_groups.yml`; each group needs one
  focus company, approved roles/statuses, and no duplicate peers.
- Treat screener-derived peer candidates as draft until reviewed
  company-by-company.

- Keep hosted Python/SQLite public deployment paused.

Deferred:

- Fundamental frameworks tab and generated framework JSON until the external
  `oslo-quant` framework screener is ready and its output contract is reviewed.

## Key Docs

- `README.md`: concise current-state overview.
- `docs/roadmap.md`: current priorities and planned sprints.
- `docs/static-github-pages-remake.md`: static architecture notes.
- `docs/watchlist-edit-workflow.md`: watchlist edit procedure.
- `docs/links-and-resources.md`: external links and source notes.
- `docs/deployment-sharing.md` and `docs/hosted-public-access-runbook.md`:
  legacy hosted-backend reference only.

## Verification Baseline

```bash
python3 -m py_compile app/server.py scripts/build_static_site_data.py
python3 -m py_compile scripts/validate_static_inputs.py
python3 scripts/validate_static_inputs.py
node --check app/static/app.js
node --check docs/app.js
```

When the local server is running:

```bash
curl -s http://127.0.0.1:8765/api/watchlist-overview | python3 -m json.tool
curl -s "http://127.0.0.1:8765/api/fundamentals?symbols=MOWI.OL" | python3 -m json.tool
curl -s "http://127.0.0.1:8765/api/technical-indicators?universe=watchlist" | python3 -m json.tool
curl -s "http://127.0.0.1:8765/api/event-monitoring" | python3 -m json.tool
```

After user-visible updates:

```bash
scripts/open_in_safari.sh
```

No next-stage prompt is needed now. Resume from operator usage feedback.
