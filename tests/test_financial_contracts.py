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
                mostRecentQuarter=int(datetime(2026, 6, 30, tzinfo=timezone.utc).timestamp()),
                componentCurrencies={"enterpriseValue": "NOK", "marketCap": "NOK", "totalDebt": currency, "totalCash": currency})


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


@pytest.mark.parametrize("pair,inverted", [("NOK/USD", False), ("EUR/NOK", False), ("USD/NOK", True), ("USDNOK=X", True), ("USD/NOK", "false")])
def test_wrong_fx_direction_cannot_qualify_coincident_numeric_bridge(pair, inverted):
    fx = dict(rate=10, pair=pair, inverted=inverted, source="fixture", fetched_at=datetime.now(timezone.utc).isoformat())
    assert ev_currency_contract(evidence("USD", 6000), PERIOD, fx)["status"] == "gated-incompatible-fx-direction"


def test_explicit_reverse_pair_with_inverted_rate_is_valid():
    fx = dict(rate=10, pair="NOKUSD=X", inverted=True, source="fixture", fetched_at=datetime.now(timezone.utc).isoformat())
    assert ev_currency_contract(evidence("USD", 6000), PERIOD, fx)["status"] == "screening-currency-consistent"


@pytest.mark.parametrize("field", ["marketCap", "totalDebt", "totalCash", "enterpriseValue"])
def test_component_currency_mismatch_is_withheld(field):
    info = evidence(); info["componentCurrencies"][field] = "EUR"
    assert ev_currency_contract(info, PERIOD, {})["status"] == "gated-incompatible-component-currencies"


def test_partial_q3_cannot_mask_june_balance_and_cashflow():
    row = {"symbol": "NOD.OL", "quarterlyStatements": {"periods": [
        {"periodEnd": "2026-09-30", "values": {"totalRevenue": 200}},
        {"periodEnd": PERIOD, "values": {"totalDebt": 100, "operatingCashFlow": 10}}]}}
    result = server.apply_financial_contracts(row)["financialFilingCoverage"]
    assert result["latest_period_end"] == "2026-09-30"
    assert result["status"] == "behind-known-release"
    assert result["tables"]["income"]["status"] == "provider-covers-known-release"
    assert result["tables"]["balance"]["status"] == "behind-known-release"
    assert result["tables"]["cashflow"]["status"] == "behind-known-release"


def historical_row(symbol="CONTROL.OL"):
    return {"symbol": symbol, "fetchedAt": "2026-10-01T12:00:00Z",
        "sourceFetchedAt": "2026-10-01T12:00:00Z", "financialInputEvidence": evidence("USD", 6000),
        "quarterlyStatements": {"periods": [{"periodEnd": PERIOD, "values": {
            "totalRevenue": 100, "totalDebt": 600, "operatingCashFlow": 10}}]},
        "ttmEbitdaPeriodEnd": PERIOD, "enterpriseToEbitda": 3,
        "enterpriseToEbitdaInputs": {"value": 3, "fxRate": 10, "fxPair": "USDNOK=X",
            "fxSource": "deterministic fixture", "fxFetchedAt": "2026-10-01T11:00:00Z"},
        "multipleSourceMetadata": {"enterpriseToEbitda": {"value": 3}}}


def test_old_valid_cross_currency_history_uses_observation_time():
    row = historical_row()
    observed = server.own_history_observation({"payload": json.dumps(row), "fetched_at": row["fetchedAt"]})
    assert observed["payload"]["enterpriseToEbitda"] == 3
    assert observed["payload"]["enterpriseValueCurrencyContract"]["status"] == "screening-currency-consistent"
    # Exactly the same old FX is not acceptable as a current observation.
    assert server.apply_financial_contracts(copy.deepcopy(row))["enterpriseToEbitda"] is None


def test_pre_release_nod_history_has_no_lookahead():
    row = historical_row("NOD.OL")
    observed = server.own_history_observation({"payload": json.dumps(row), "fetched_at": row["fetchedAt"]})
    assert observed["payload"]["financialFilingCoverage"]["status"] == "unverified"
    assert observed["payload"]["financialFilingCoverage"]["issuer_release"] is None
    assert observed["payload"]["enterpriseToEbitda"] == 3
    assert server.apply_financial_contracts(copy.deepcopy(row))["financialFilingCoverage"]["status"] == "behind-known-release"


def test_historical_future_fx_is_still_withheld():
    row = historical_row()
    row["enterpriseToEbitdaInputs"]["fxFetchedAt"] = "2026-10-02T11:00:00Z"
    observed = server.own_history_observation({"payload": json.dumps(row), "fetched_at": row["fetchedAt"]})
    assert observed["payload"]["enterpriseToEbitda"] is None


def test_populated_dofg_anomaly_not_missing_evidence_fallback():
    fixture = json.loads((Path(__file__).parent / "fixtures/dofg-populated-bridge.json").read_text())
    result = ev_currency_contract(fixture["info"], fixture["period_end"], fixture["fx"], server.parse_utc(fixture["evaluated_at"]))
    assert result["status"] == "gated-unreconciled-ev-components"
    assert result["debt"] == 1718000000
    assert result["cash"] == 343000000
    assert result["residual"] < -10000000000


def test_balance_only_new_quarter_withholds_pe_and_pb():
    row = {"symbol": "NOD.OL", "trailingPE": 20, "priceToBook": 4,
        "multipleSourceMetadata": {"trailingPE": {"value": 20}, "priceToBook": {"value": 4}},
        "quarterlyStatements": {"periods": [
            {"periodEnd": "2026-09-30", "values": {"totalDebt": 100}},
            {"periodEnd": PERIOD, "values": {"totalRevenue": 200, "operatingCashFlow": 10}}]}}
    result = server.apply_financial_contracts(row)
    assert result["financialFilingCoverage"]["status"] == "behind-known-release"
    assert result["trailingPE"] is None
    assert result["priceToBook"] is None


def test_all_quarterly_tables_cover_known_release():
    row = {"symbol": "NOD.OL", "quarterlyStatements": {"periods": [
        {"periodEnd": "2026-09-30", "values": {"totalRevenue": 200, "totalDebt": 100, "operatingCashFlow": 10}}]}}
    assert server.apply_financial_contracts(row)["financialFilingCoverage"]["status"] == "provider-covers-known-release"
