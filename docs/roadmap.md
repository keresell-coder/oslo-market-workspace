# Roadmap

## Current MVP

- Local web app with watchlist, fundamentals screener, embedded Oslo Screener tab, and source-quality notes.
- SQLite-backed ticker database and editable watchlist.
- Cached `yfinance` fundamentals for `.OL` tickers where Yahoo Finance has coverage.
- Descriptive benchmark tab with manual peer-group seeds and own-history snapshot collection.

## Next Sprint

1. Establish GitHub repository under `keresell-coder/oslo-market-workspace`.
2. Add an Oslo ticker universe importer.
3. Add a conservative NewsWeb monitor:
   - ticker-specific links first
   - automated collection only after a stable public endpoint or acceptable fetch pattern is confirmed
4. Improve data provenance:
   - per-field source labels
   - stale-data warnings
   - manual override fields for values that free data cannot supply
5. Replace absolute valuation labels with benchmark-driven scoring only:
   - no cheap/expensive/neutral flagging from standalone multiples
   - require peer group, sector context, and own-history comparison
   - display criteria and data confidence next to any future score
6. Review and curate peer groups:
   - verify whether each international peer is actually comparable
   - add Oslo sector groups where public data allows it
   - tag peer groups as draft, reviewed, or trusted

## Peer Benchmarking Sprint

Peer benchmarking has started as a descriptive layer. It should not become a scoring layer until peer groups and source coverage are reviewed.

Initial design:

- Define peer groups by sector and manual tags.
- Allow each company to be compared against selected peers.
- Show median, high, low, and rank for:
  - TTM P/E
  - forward P/E
  - P/B
  - EV/EBITDA
  - dividend yield
  - market cap
  - target-price upside where available
- Add sector-specific extensions:
  - shipping: NAV discount/premium, fleet exposure, day-rate sensitivity
  - seafood: harvest volume, EBIT/kg, biomass, feed cost exposure
  - oil service: backlog, book-to-bill, net debt/EBITDA
  - banks/financials: P/B, ROE, CET1 where available
  - real estate: P/NAV, LTV, occupancy, WAULT

Important constraint: some sector metrics require company reports, broker estimates, or manual inputs. The app should show missing data honestly rather than manufacturing values.

No valuation flag should be shown unless its peer group, sector benchmark, own-history range, source timestamp, and confidence level are visible.
