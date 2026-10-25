# Interpretation contract repair — 25 October 2026

This bounded repair preserves provider facts, financial/EV gates, trading rules, schedules and the dormant tracking ledger. It changes which comparisons can be inferred from those facts.

## Quotes
The prominent watchlist date is `priceObservedAt`, never `fetchedAt`. Missing quote dates/currencies remain unknown. Collection dates remain in source details. A fresh collection does not make the quote or analyst estimate fresh.

## Targets
Raw provider target mean/low/high remain in source details, explicitly unqualified. Neither missing target dates nor an aggregate supplied by an older endpoint can bypass the comparison gate. Raw provider fundamentals no longer calculate unsupported target/price upside, including re-enriched caches.

A comparable target requires a positive finite target and price, a known nonfuture quote date, exact matching currency, source URL, reviewed/verified/trusted source status, estimate `as_of_date`, explicit `target_horizon_date`, and `valid_until`. The validity date must come from a documented source review, not from collection time or an invented universal freshness threshold. The quote and current date must be within that window; validity cannot extend beyond the horizon. Aggregated rows must share exact vintage, horizon and currency. Different cohorts are withheld rather than averaged. The resulting median/price gap is descriptive, not a calibrated return forecast; broker references may overlap.

The new optional date fields are supported in the manual source editor/API and `data/manual_consensus.yml`, with schema migration and backward-compatible cache import. They are deliberately empty for Yahoo rows. No missing dates or horizons were invented. Sources carry separate `collectionStatus` and estimate `staleStatus`. Unknown vintage cannot receive an affirmative estimate-freshness label.

## Peers
`metric_summary` now requires source-reviewed, metric-specific `multipleSourceMetadata[metric].comparisonBasis`: `periodEnd`, `periodBasis` (e.g. TTM versus forward), `accountingScope`, `economicGroup`, `sourceUrl`, and `reviewStatus`. Period/basis/scope/group must match the focus. Dimensionless ratios do not require equal reporting currencies. Nonfinite numbers are excluded. A reviewed group alone does not satisfy the contract.

**Coverage limitation:** existing provider feeds do not populate these metric-level contracts. This repair intentionally withholds their peer medians/relative gaps and `minimumDataMet`, retaining raw company/peer facts. It does not introduce a new verified peer-data ingestion or adjudication workflow. Adding supported, source-linked comparison-basis ingestion is separate follow-up work; do not hand-edit generated JSON and claim automatic coverage.

The frontend also rejects legacy ungated target/peer comparison payloads, so publishing new assets before the next data refresh cannot resurrect the old inferences. Dashboard card counts explicitly do not represent the independent CSV technical watchlist.

## Verification boundary
Unit, renderer and syntax checks cover normal, stale, missing, incompatible, nonfinite and legacy payloads; all 66 saved undated target rows remain date-unknown. This is not a live deployment, browser usability certification or proof of investment performance. Independent review precedes any remote publication.
