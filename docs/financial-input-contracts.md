# Financial input contracts — first bounded repair

This changes validation and withholding, not formulas, peer policy or financial figures.
No primary financial values have been refreshed or replaced by this patch.

- `sourceFetchedAt` is provider retrieval, `priceObservedAt` is quote observation,
  statement period ends are accounting periods, and issuer publication dates are
  maintained separately in `app/financial_contracts.py`. Nordic's issuer quarterly
  archive shows Q3 2026 published 22 October, period ending 30 September.
  The registry records release availability only, not verification of the figures.
  Unknown issuer releases remain unverified; this is not a complete filing calendar.
- Known newer filings require coverage from each of the income, balance and cash-flow tables; a partial new quarter gates current financial multiples; TTM denominators must also
  cover that period. Cache reads, retained-on-error rows, own-history inputs and
  peer inputs use the same guard. Primary-review state remains separate.
- EV/EBITDA and EV/revenue require explicit quote/reporting currencies, positive
  EV/market cap, nonnegative separately labelled debt/cash, matching balance/TTM
  periods and usable FX when needed. Provider EV is compared with market cap plus
  converted net debt; it is never replaced. Tolerance is 1% of converted net debt,
  with a one-currency-unit floor, inclusive at the boundary. Cross-currency FX
  needs matching reporting-to-quote pair direction (or explicitly inverted reverse
  pair), explicit component currency labels and source/retrieval evidence within
  24h of evaluation. This is an arithmetic screening
  check, not proof of accounting-definition, restricted-cash or lease treatment.
- Old cached rows without component evidence withhold EV ratios. The original
  provider and withheld values remain audit data; they are not peer observations.
  Source-trust validation rejects candidates leaking guarded ratios.

Regression inputs are frozen in `tests/fixtures/financial-input-audit.json` from
commit d9692a02e3f53f767abce521d3fc00c1bd37f1a5 / snapshot
e221619ea13a49b0a12bc9a6d76b4779. Offline before/after JSON and HTML are in
`docs/review-evidence/`; these show the guard, not a source refresh.

Verified locally: 69 Python tests; 9 Node tests; Python compilation; syntax checks
for both frontend copies; git diff whitespace check. No live provider refresh or
Safari review was performed in this repair branch. Review precedes merge/deploy.

After approval: merge, run `.github/workflows/static-data.yml` on main (true refresh,
staged validation), inspect the generated commit and Pages deployment, then fetch
live health/manifest/fundamentals/peer/overview/detail outputs for the same snapshot.
Confirm DOFG unresolved EV ratios are absent from peer medians and summaries, and
Nordic is either explicitly behind the known release or has actually obtained Q3
provider periods. Passing coverage still does not reconcile EBITDA definitions.
A failed refresh retains prior content and publishes failure health; do not call
that a refreshed/reconciled financial dataset. Existing generated data in this PR
is deliberately unchanged. Cloud project-plan updates are coordinated separately.

Review fixes: historical observations evaluate contracts as of their own stored
retrieval time, retaining valid older FX and avoiding release-date look-ahead.
Historical export retains contract evidence for reproducibility. Current reads
still evaluate current coverage; a historical observation is not fresh current data.
The populated DOFG bridge fixture is explicitly synthetic: audit-supplied amounts
plus FX=10 and deterministic timestamps; it independently triggers an inconsistent
component bridge, while the original frozen rows demonstrate legacy missing-evidence
withholding. Both are distinct from primary accounting reconciliation.
MOWI's saved row also lacks bridge evidence and its EV ratios are conservatively
withheld (previous 7.7954767x EV/EBITDA and 1.8489337x EV/revenue); this does not
assert those earlier values were wrong.
