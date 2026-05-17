# Primary Report Verification

Quarterly statement history currently starts from Yahoo/yfinance quarterly
income statement, balance sheet, and cash-flow tables. Those rows remain
screening-grade until a specific period is reviewed against a primary company
report.

## Scope

This workflow is a manual/source-linked review tracker. It does not scrape,
parse, import, or infer company report values.

Primary sources can include:

- company quarterly reports
- company annual reports
- stock-exchange report PDFs
- company investor-relations report tables

Do not use generic sector labels, current yfinance summary fields, peer rows,
or sector KPI placeholders to fill missing quarterly statement values. Missing
data stays missing.

## Review Statuses

- `unverified`: no stored primary report review for the period.
- `needs-review`: a primary source is located, but row/value mapping has not
  been checked.
- `reviewed-match`: the period was checked against a primary report source URL
  and the stored yfinance row mapping/value is acceptable for screening context.
- `reviewed-difference`: the primary report differs from the provider row or
  the row mapping is unclear.
- `not-found`: a suitable primary source could not be found.

Only `reviewed-match` with a source URL counts as a primary-reviewed period.
Even then, it only improves source quality for that period. It does not create
recommendation logic, a valuation verdict, or any cheap/expensive/fair/neutral
standalone multiple label.

## App Behavior

- `/api/fundamentals` attaches `primaryReportVerification` metadata to each
  `quarterlyStatementHistory` block.
- Own history shows the primary-review count in the Source/gate column.
- Each quarterly statement period shows its primary-review status.
- Own history includes a small form for recording a primary-review row for an
  existing yfinance-dated period.
- Stored review rows are available through `/api/quarterly-statement-reviews`.

The app does not backfill values from primary reports. If a yfinance row or
period is missing, it remains missing until a separately scoped primary-report
data-entry path exists.

## API

Read review rows:

```bash
curl -s "http://127.0.0.1:8765/api/quarterly-statement-reviews?symbol=MOWI.OL" | python3 -m json.tool
```

Record a source-linked review row:

```bash
curl -s -X POST http://127.0.0.1:8765/api/quarterly-statement-reviews \
  -H "content-type: application/json" \
  -d '{
    "symbol": "MOWI.OL",
    "periodEnd": "2025-12-31",
    "reviewStatus": "needs-review",
    "sourceName": "Company quarterly report",
    "sourceUrl": "https://example.com/report.pdf",
    "reportPeriod": "Q4 2025",
    "reviewerNote": "Source located; row mapping not completed.",
    "limitationNote": "Do not treat as primary matched yet."
  }' | python3 -m json.tool
```

Use `reviewed-match` only after the source URL and row/value mapping have been
checked.
