"""Conservative input contracts. Passing checks never verifies accounting definitions."""
from datetime import date, datetime, timezone
import math
import re

# Manually observed issuer release; not a forecast or an automatic primary-data replacement.
KNOWN_FILINGS = {"NOD.OL": {
    "period_end": "2026-09-30", "published_on": "2026-10-22",
    "observed_at": "2026-10-24T20:54:00+00:00",
    "source_url": "https://www.nordicsemi.com/Investor-Relations/Reports/Quarterly",
    "scope": "Issuer release availability only; values and accounting definitions unverified",
}}


def filing_coverage(symbol, periods, now=None):
    today = (now or datetime.now(timezone.utc)).date()
    valid = []
    for value in periods:
        try:
            end = date.fromisoformat(value)
            if end > today:
                raise ValueError("future")
            valid.append(end.isoformat())
        except (ValueError, TypeError):
            return {"status": "invalid-period", "latest_period_end": None, "issuer_release": None}
    release = KNOWN_FILINGS.get(symbol)
    active = release if release and date.fromisoformat(release["published_on"]) <= today else None
    latest = max(valid) if valid else None
    status = "unverified"
    if active:
        status = "provider-covers-known-release" if latest and latest >= active["period_end"] else "behind-known-release"
    return {"status": status, "latest_period_end": latest, "issuer_release": active,
            "limitation": "Retrieval time is separate from filing coverage. Coverage does not verify values or definitions; unknown issuer dates remain unverified."}


def ev_currency_contract(info, period_end, fx):
    """Check provider EV against separately labelled net-debt components; never replace EV."""
    quote, financial = info.get("currency"), info.get("financialCurrency")
    result = {"status": "gated-unverified-ev-currency", "quote_currency": quote,
              "financial_currency": financial, "unit": "currency units (not millions)",
              "period_end": period_end, "provider": "Yahoo Finance via yfinance",
              "tolerance_fraction": 0.01,
              "limitation": "EV currency/component bridge is unverified. No corrected valuation is substituted; passing arithmetic does not reconcile leases, minorities, restricted cash or EBITDA definitions."}
    def number(key):
        value = info.get(key)
        return value if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) else None
    ev, cap, debt, cash = (number(k) for k in ("enterpriseValue", "marketCap", "totalDebt", "totalCash"))
    result.update(enterprise_value=ev, market_cap=cap, debt=debt, cash=cash,
                  debt_cash_currency=financial, fx=dict(fx))
    if not all(isinstance(c, str) and re.fullmatch(r"[A-Z]{3}", c) for c in (quote, financial)) or any(v is None for v in (ev, cap, debt, cash)):
        return result
    if ev <= 0 or cap <= 0 or debt < 0 or cash < 0:
        return result
    try:
        balance_end = datetime.fromtimestamp(info["mostRecentQuarter"], timezone.utc).date().isoformat()
    except (KeyError, ValueError, TypeError, OverflowError, OSError):
        return result
    result["balance_period_end"] = balance_end
    if not period_end or balance_end != period_end:
        result["status"] = "gated-incompatible-input-periods"
        return result
    rate = 1.0 if quote == financial else fx.get("rate")
    if not isinstance(rate, (int, float)) or not math.isfinite(rate) or rate <= 0:
        result["status"] = "gated-missing-fx-rate"
        return result
    if quote != financial:
        try:
            fetched = datetime.fromisoformat(str(fx.get("fetched_at")).replace("Z", "+00:00"))
            age = (datetime.now(timezone.utc) - fetched).total_seconds() if fetched.tzinfo else -1
            if not 0 <= age <= 86400 or not fx.get("source") or not fx.get("pair"):
                return result
        except (ValueError, TypeError):
            return result
    expected = cap + (debt - cash) * rate
    # Tolerance is relative to net debt (not market cap, which could mask mixed currencies).
    tolerance = max(1.0, abs((debt - cash) * rate) * 0.01)
    result.update(expected_ev_for_currency_check=expected, residual=ev-expected, tolerance=tolerance)
    if abs(ev - expected) > tolerance:
        result["status"] = "gated-unreconciled-ev-components"
    else:
        result["status"] = "screening-currency-consistent"
    return result
