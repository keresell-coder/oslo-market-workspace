# Watchlist And Peer Edit Workflow

This project is now a static GitHub Pages beta. The public browser app is
read-only and must not contain GitHub write tokens. Watchlist and peer edits
happen through reviewed repo changes and generated static data.

## Standard Watchlist Flow

1. Edit `data/watchlist.yml` on a `codex/` branch.
2. Keep the YAML schema valid:
   - `watchlist: Core Watchlist`
   - `items:` list of `symbol`, `name`, `sector`, `industry`, and `note`
   - Oslo-listed symbols use uppercase `.OL` suffixes
   - unknown notes stay as `''`
3. Run input validation:
   - `python3 scripts/validate_static_inputs.py`
4. Regenerate static data:
   - `python3 scripts/build_static_site_data.py`
5. Run local validation:
   - `python3 -m py_compile app/server.py scripts/build_static_site_data.py`
   - `python3 -m py_compile scripts/validate_static_inputs.py`
   - `node --check app/static/app.js`
   - `node --check docs/app.js`
   - `python3 -m json.tool docs/data/manifest.json`
   - `python3 -m json.tool docs/data/watchlist-overview.json`
   - `python3 -m json.tool docs/data/technical-indicators-watchlist.json`
6. Open a pull request to `main`.
7. After merge, run the **Static GitHub Pages data** workflow manually or wait
   for the next scheduled run.
8. Verify the public Pages URL, manifest timestamp, Watchlist row count, and
   affected rows after Pages cache clears.

## Peer Group Flow

Edit `data/peer_groups.yml` with the same branch, validation, PR, workflow, and
public verification path.

Keep the schema conservative:

- each group has `group_key`, `name`, `status`, `curator_note`, `source`, and
  `items`
- status is one of `draft`, `reviewed`, or `trusted`
- each group has exactly one `focus company`
- roles are one of `focus company`, `Oslo peer`, `Nordic peer`,
  `European peer`, `international peer`, or `sector index/proxy`
- do not duplicate a peer symbol inside a group
- do not promote screener-derived candidates beyond `draft` until reviewed
  company-by-company

Simple supported operations:

- add a candidate peer to a covered company
- remove an unsuitable peer
- change peer role, status, note, or source label
- create a new draft group when a covered watchlist company has no peer group

Screener output, yfinance industry, and sector labels are only candidate
sources. They must not automatically create reviewed peer context.

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

## Peer Edit Prompt

```text
Please edit data/peer_groups.yml in keresell-coder/oslo-market-workspace.

Requested peer-group change:
- Add/remove/update: <describe company, peer, role/status/note/source>

Keep the YAML schema valid:
- status is draft/reviewed/trusted
- exactly one focus company per group
- peer roles use the existing role labels
- no duplicate symbols inside a group
- screener-derived candidates stay draft until reviewed company-by-company

Preserve the app guardrails:
- no buy/sell investment advice
- no standalone cheap/expensive/fair/neutral valuation labels
- missing data stays missing
- source, freshness, confidence, and limitation notes remain visible

Run python3 scripts/validate_static_inputs.py, regenerate static data, run the
standard validation checks, update relevant docs if workflow/status changes,
and open a PR from a codex/ branch. After merge, run the Static GitHub Pages
data workflow or wait for the next scheduled refresh, then verify the public
Pages URL and affected benchmark rows.
```

## Current Scope

The low-risk edit path consists of `scripts/validate_static_inputs.py`, stricter
peer-group validation, this repeatable workflow, and generated JSON review.
Public Pages remains read-only.
