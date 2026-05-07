# Operator Refresh Checklist

Use this before sharing a beta view or discussing the app with another user.

The app remains screening-grade. Refreshing data does not validate it, create
investment advice, or turn provider rows into verified consensus.

## Refresh Order

1. Open the Start tab and review the operator refresh checklist.
2. Refresh Watchlist.
3. Refresh Fundamentals for the watchlist universe.
4. Refresh Own history for the watchlist universe.
5. Refresh Technical indicators for the watchlist universe.
6. Refresh News/Events on demand.
7. Open the separate RSI14 screener tab and confirm the dashboard date and
   source-generation freshness.
8. Open Sources if source limitations or provider paths need to be explained.

## What To Check

- Each refreshed tab should show a refresh status strip with last successful app
  refresh, source timestamp when available, source/cache details, and errors or
  warnings.
- Fundamentals/yfinance errors mean affected rows remain screening-grade or
  stale until checked against primary/company sources.
- Own-history quarterly statement periods remain not-primary-verified until a
  source-linked primary-report review row is stored.
- Consensus/target/rating data remains provider/source-row data unless a
  reviewed manual/source row exists.
- Benchmarks require reviewed/trusted peer groups and source-linked sector KPI
  inputs before the context should be treated as reviewed.
- News/Events uses on-demand NewsWeb rows plus manual rows. Digest duplicate and
  correction grouping is heuristic, and fetch errors stay visible.
- Missing data stays missing. Do not infer NAV/fleet, P/NAV, EBIT/kg, backlog,
  ROE/CET1, LTV/WAULT, or statement-history values from sector labels.

## Out Of Scope

- Scheduled NewsWeb automation.
- Buy/sell/hold recommendation logic.
- Cheap/expensive/fair/neutral standalone valuation labels.
- Editing Oslo Screener repositories.

