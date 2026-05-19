# Watchlist Edit Workflow

This project is now a static GitHub Pages beta. The public browser app is
read-only and must not contain GitHub write tokens. Watchlist edits happen
through reviewed repo changes and generated static data.

## Standard Flow

1. Edit `data/watchlist.yml` on a `codex/` branch.
2. Keep the YAML schema valid:
   - `watchlist: Core Watchlist`
   - `items:` list of `symbol`, `name`, `sector`, `industry`, and `note`
   - Oslo-listed symbols use uppercase `.OL` suffixes
   - unknown notes stay as `''`
3. Regenerate static data with `python3 scripts/build_static_site_data.py`.
4. Run local validation:
   - `python3 -m py_compile app/server.py scripts/build_static_site_data.py`
   - `node --check app/static/app.js`
   - `node --check docs/app.js`
   - `python3 -m json.tool docs/data/manifest.json`
   - `python3 -m json.tool docs/data/watchlist-overview.json`
   - `python3 -m json.tool docs/data/technical-indicators-watchlist.json`
5. Open a pull request to `main`.
6. After merge, run the **Static GitHub Pages data** workflow manually or wait
   for the next scheduled run.
7. Verify the public Pages URL, manifest timestamp, Watchlist row count, and
   affected rows after Pages cache clears.

## Codex Prompt

```text
Please edit data/watchlist.yml in keresell-coder/oslo-market-workspace.

Requested watchlist change:
- Add/update/remove: <describe change>

Keep the YAML schema valid:
- watchlist: Core Watchlist
- items: list of symbol/name/sector/industry/note rows
- use uppercase .OL suffixes for Oslo-listed symbols
- keep unknown notes as ''

Preserve the app guardrails:
- no buy/sell investment advice
- no cheap/expensive/fair/neutral standalone valuation labels
- missing data stays missing
- source, freshness, confidence, and limitation notes remain visible

Regenerate static data, run the standard validation checks, update relevant
docs if the workflow/status changes, and open a PR from a codex/ branch. After
merge, run the Static GitHub Pages data workflow or wait for the next scheduled
refresh, then verify the public Pages URL and manifest.
```

## Current Example

The 19 May 2026 edit-workflow polish pass adds `BRG.OL` / Borregaard ASA to
`data/watchlist.yml`, regenerates static JSON, and keeps the public Pages edit
path as YAML plus PR plus generated data.
