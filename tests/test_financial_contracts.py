import copy
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from app import server
from app.financial_contracts import ev_currency_contract, filing_coverage

PERIOD = "2026-06-30"
NOW = datetime(2026, 10, 24, tzinfo=timezone.utc)


def evidence(currency="NOK", ev=1500):
    return dict(currency="NOK", financialCurrency=currency, enterpriseValue=ev,
                marketCap=1000, totalDebt=600, totalCash=100,
                mostRecentQuarter=int(datetime(2026, 6, 30, tzinfo=timezone.utc).timestamp()))


def test_filing_dates_are_separate():
    lagged = filing_coverage("NOD.OL", [PERIOD], NOW)
    assert lagged["status"] == "behind-known-release"
    assert lagged["issuer_release"]["published_on"] == "2026-10-22"
    assert filing_coverage("NOD.OL", ["2026-09-30"], NOW)["status"] == "provider-covers-known-release"
    assert filing_coverage("DOFG.OL", [PERIOD], NOW)["status"] == "unverified"
    assert filing_coverage("NOD.OL", [], NOW)["status"] == "behind-known-release"
    assert filing_coverage("NOD.OL", ["2999-01-01"], NOW)["status"] == "invalid-period"


@pytest.mark.parametrize("delta,passes", [(5, True), (5.001, False), (-5, True), (-5.001, False)])
def test_net_debt_tolerance(delta, passes):
    result = ev_currency_contract(evidence(ev=1500+delta), PERIOD, {})
    assert (result["status"] == "screening-currency-consistent") is passes


def test_documented_cross_currency_and_old_mixed_currency():
    fx = dict(rate=10, pair="USD/NOK", source="fixture", fetched_at=datetime.now(timezone.utc).isoformat())
    assert ev_currency_contract(evidence("USD", 6000), PERIOD, fx)["status"] == "screening-currency-consistent"
    assert ev_currency_contract(evidence("USD", 1500), PERIOD, fx)["status"] == "gated-unreconciled-ev-components"
    for rate in [None, 0, -1, float("nan")]:
        assert ev_currency_contract(evidence("USD"), PERIOD, {**fx, "rate": rate})["status"] != "screening-currency-consistent"
    assert ev_currency_contract(evidence("USD", 6000), PERIOD, {**fx, "fetched_at": None})["status"] != "screening-currency-consistent"


@pytest.mark.parametrize("key,value", [("financialCurrency", None), ("currency", None), ("totalDebt", None), ("totalCash", None), ("enterpriseValue", -1), ("financialCurrency", "Unknown"), ("mostRecentQuarter", None)])
def test_unknown_and_missing_inputs(key, value):
    info = evidence(); info[key] = value
    assert ev_currency_contract(info, PERIOD, {})["status"] != "screening-currency-consistent"


def test_incompatible_periods():
    assert ev_currency_contract(evidence(), "2026-03-31", {})["status"] == "gated-incompatible-input-periods"


def test_saved_audit_regressions_and_cached_normalization():
    source = json.loads((Path(__file__).parent / "fixtures/financial-input-audit.json").read_text())
    for symbol in ["DOFG.OL", "NOD.OL"]:
        row = copy.deepcopy(next(r for r in source["rows"] if r["symbol"] == symbol))
        guarded = server.normalize_fundamental_multiple_fields(row)
        assert guarded["enterpriseToEbitda"] is None
        assert guarded["enterpriseToRevenue"] is None
        assert guarded["multipleSourceMetadata"]["enterpriseToEbitda"]["value"] is None
        assert guarded["enterpriseToEbitdaInputs"]["value"] is None
        if symbol == "NOD.OL":
            assert guarded["financialFilingCoverage"]["status"] == "behind-known-release"
        assert server.apply_financial_contracts(copy.deepcopy(guarded)) == guarded


@pytest.mark.parametrize("value", [None, 0, -10])
def test_existing_nonpositive_denominator_gate_survives(value):
    class Ticker: pass
    from unittest.mock import patch
    with patch.object(server, "ttm_statement_value", return_value=(value, "EBITDA", PERIOD)), patch.object(server, "yfinance_fx_rate", return_value={"rate": 1}):
        assert server.enterprise_to_ebitda_summary(Ticker(), evidence(), "2026-10-24T12:00:00Z")["value"] is None


def test_valid_bridge_survives_and_peer_inputs_are_withheld():
    row = {"symbol": "CONTROL.OL", "financialInputEvidence": evidence(),
           "quarterlyStatements": {"periods": [{"periodEnd": PERIOD}]},
           "ttmEbitdaPeriodEnd": PERIOD,
           "enterpriseToEbitda": 3, "enterpriseToRevenue": 1.5,
           "enterpriseToEbitdaInputs": {"value": 3, "fxRate": 1},
           "multipleSourceMetadata": {"enterpriseToEbitda": {"value": 3},
             "enterpriseToRevenue": {"value": 1.5, "inputs": {"denominatorPeriodEnd": PERIOD}}}}
    assert server.apply_financial_contracts(copy.deepcopy(row))["enterpriseToEbitda"] == 3
    row["financialInputEvidence"]["financialCurrency"] = "USD"
    guarded = server.apply_financial_contracts(row)
    assert server.numeric_metric(guarded, "enterpriseToEbitda", True) is None
    assert server.numeric_metric(guarded, "enterpriseToRevenue", True) is None
