"""Fail-closed interpretation contracts. Collection clocks are not evidence dates."""
from datetime import datetime, timezone
import math


def day(value):
    try:
        return datetime.fromisoformat(str(value).replace('Z', '+00:00')).date()
    except (ValueError, TypeError):
        return None


def positive(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value > 0


def estimate_status(row, now=None):
    today = (now or datetime.now(timezone.utc)).date()
    vintage, horizon, valid = (day(row.get(k)) for k in ('as_of_date', 'target_horizon_date', 'valid_until'))
    if not vintage:
        return 'estimate-date-unknown'
    if vintage > today:
        return 'invalid-estimate-date'
    if not horizon or not valid:
        return 'dated-estimate-validity-unverified'
    if not vintage <= valid <= horizon or horizon <= vintage:
        return 'invalid-estimate-contract'
    if today > valid:
        return 'estimate-review-expired'
    return 'within-source-review-window'


def target_comparison(fundamental, rows, now=None):
    """Only compare reviewed, dated, same-currency/horizon/vintage source rows.

    valid_until is a source-linked reviewer validity date, not an inferred age
    threshold. No FX conversion or implicit 12-month analyst horizon is assumed.
    """
    now = now or datetime.now(timezone.utc)
    price, currency, quote_day = fundamental.get('price'), fundamental.get('currency'), day(fundamental.get('priceObservedAt'))
    candidates, excluded = [], []
    for row in rows:
        reason = None
        if not positive(row.get('target_mean')):
            reason = 'missing-positive-target'
        elif any(row.get(key) is not None and not positive(row[key]) for key in ('target_low', 'target_high')):
            reason = 'invalid-target-interval'
        elif (row.get('target_low') is not None and row['target_low'] > row['target_mean']) or (row.get('target_high') is not None and row['target_high'] < row['target_mean']):
            reason = 'contradictory-target-interval'
        elif estimate_status(row, now) != 'within-source-review-window':
            reason = estimate_status(row, now)
        elif row.get('review_status') not in {'reviewed', 'verified', 'trusted'} or not row.get('source_url'):
            reason = 'target-not-source-reviewed'
        elif not currency or row.get('target_currency') != currency:
            reason = 'target-currency-incompatible-or-unknown'
        elif not positive(price) or not quote_day or quote_day > now.date():
            reason = 'price-date-or-value-unverified'
        elif not day(row['as_of_date']) <= quote_day <= day(row['valid_until']):
            reason = 'price-outside-estimate-review-window'
        if reason:
            excluded.append({'source': row.get('source'), 'reason': reason})
        else:
            candidates.append(row)
    bases = {(r['as_of_date'], r['target_horizon_date'], r['target_currency']) for r in candidates}
    if len(bases) > 1:
        excluded.extend({'source': r.get('source'), 'reason': 'incompatible-target-vintage-or-horizon'} for r in candidates)
        candidates = []
    values = sorted(r['target_mean'] for r in candidates)
    # Stable midpoint: statistics.median can overflow for two large finite values.
    target = (values[len(values)//2] if len(values) % 2 else values[len(values)//2-1] + (values[len(values)//2] - values[len(values)//2-1])/2) if values else None
    upside = (target / price - 1) * 100 if target is not None else None
    if upside is not None and not math.isfinite(upside):
        excluded.extend({'source': r.get('source'), 'reason': 'nonfinite-target-price-gap'} for r in candidates)
        candidates, target, upside = [], None, None
    return {'target': target,
            'targetLow': min([r['target_low'] for r in candidates if positive(r.get('target_low'))], default=None),
            'targetHigh': max([r['target_high'] for r in candidates if positive(r.get('target_high'))], default=None),
            'targetUpsidePct': upside,
            'eligibleRows': len(candidates), 'excludedRows': excluded,
            'evaluatedAt': now.isoformat(),
            'estimateAsOf': candidates[0]['as_of_date'] if candidates else None,
            'horizonDate': candidates[0]['target_horizon_date'] if candidates else None,
            'validUntil': min(r['valid_until'] for r in candidates) if candidates else None,
            'status': 'source-reviewed-comparable-targets' if candidates else 'target-comparison-withheld',
            'method': 'Dated, source-reviewed rows with matching currency, vintage and horizon; descriptive target/price gap, not expected return. Raw unqualified targets remain in source details.'}


def peer_basis(payload, key):
    basis = payload.get('multipleSourceMetadata', {}).get(key, {}).get('comparisonBasis') or {}
    required = ('periodEnd', 'periodBasis', 'accountingScope', 'economicGroup', 'sourceUrl')
    if basis.get('reviewStatus') not in {'reviewed', 'verified', 'trusted'} or any(not basis.get(k) for k in required):
        return None
    if not day(basis['periodEnd']) or day(basis['periodEnd']) > datetime.now(timezone.utc).date():
        return None
    return tuple(basis[k] for k in required[:-1])


def peer_compatible(focus, peer, key):
    a, b = peer_basis(focus, key), peer_basis(peer, key)
    return bool(a and b and a == b)
