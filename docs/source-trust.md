# Source trust and publication

The static publisher collects in a temporary SQLite database and stages a whole
candidate dataset. Every endpoint and manifest carries one `snapshotId`. The
gate verifies watchlist identity/coverage, real retrieval dates (within 24 hours,
never future), price availability, quote/statement dates, peer/overview agreement,
and withheld technical labels. Empty peer payloads do not count as loaded peers.
Only a valid candidate replaces `docs/data/`. An invalid attempt preserves prior
data/history, writes failure to `docs/health.json`, and fails Actions. The workflow
stages only that health file after failure, including a partial filesystem error.

[Public health](https://keresell-coder.github.io/oslo-market-workspace/health.json)
uses `oslo_workspace.health.v1`: `snapshot_id`, `generated_at`, `source_fetched_at`,
`source_observation_start/end`, `expected_session`, `valid_until`, `status`,
`coverage`, `statements`, `issues`, and separate technical/news source records.
The browser compares health, manifest, endpoint snapshot IDs and expiration; an
old retained dataset cannot show current signal or position-size labels.

Technical CSV rows are checked independently against the completed Oslo cash
session and matched to the producer's public health snapshot and CSV SHA-256.
Missing, stale, invalid, provisional, legacy, or unmatched data have labels and
sizing withheld. The shared calendar module is vendored from oslo-screener and
requires annual verification after 2026. Parsed dashboard HTML remains a source
link; its cards lack per-card provenance and are not alternate signal coverage.

`sourceFetchedAt` is retrieval time. `priceObservedAt` belongs to the actual
`regularMarketPrice`; fallback quotes have unknown observation time. Provider
consensus retains retrieval time across cache enrichment, while unknown estimate
dates stay blank. Statement ends never imply primary filing verification.

`docs/data/fundamentals-history.json` persists one latest retrieval per symbol and
UTC date across clean builds. It can bootstrap the one stored previous retrieval,
but never invents missing days. A metric needs five distinct daily observations
spanning at least 90 calendar days before history context is enabled. This is a
disclosed coverage policy, not a calibrated edge or a representative valuation
cycle. Primary-report review and sector-KPI coverage remain separate unfinished
research work.

Validation: `python3 -m pytest -q`, `node --test tests/*.test.cjs`,
`python3 -m py_compile app/server.py app/market_health.py scripts/*.py`, and
`node --check app/static/app.js`. PR/main CI runs the meaningful regressions.
Live staged collection on 2026-09-09 retrieved all 15 watchlist companies and
76 quarterly statement periods (zero primary reviewed); Sep 8 quote observations
matched the expected completed session. The legacy technical feed was correctly
withheld. Five empty configured peers require source/ticker review; none were
silently substituted.
