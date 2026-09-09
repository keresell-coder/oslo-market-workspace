import copy
import csv
import hashlib
import io
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app import server
from scripts import build_static_site_data as build
from scripts import source_trust as trust

NOW = datetime(2026, 9, 9, 8, 0, tzinfo=timezone.utc)
FETCHED = "2026-09-09T07:55:00+00:00"
OBSERVED = "2026-09-08T14:30:00+00:00"


def bundle(path):
    row = {"symbol": "MOWI.OL", "sourceFetchedAt": FETCHED, "fetchedAt": FETCHED,
           "priceObservedAt": OBSERVED, "price": 200,
           "quarterlyStatements": {"periods": [{"periodEnd": "2026-06-30"}]}}
    documents = {
        "fundamentals-watchlist.json": {"rows": [row], "errors": []},
        "watchlist-overview.json": {"rows": [{"symbol": "MOWI.OL", "peerContext": {"loadedPeerCount": 1, "groupName": "Seafood"}}]},
        "technical-indicators-watchlist.json": {"rows": [{"symbol": "MOWI.OL", "signal": "NEUTRAL"}],
            "sourceHealth": {"status": "current", "actionable": True, "expected_session": "2026-09-08", "valid_until": "2026-09-09T16:45:00+02:00"}},
        "benchmarks/MOWI.OL.json": {"groups": [{"name": "Seafood", "items": [row, {"symbol": "SALM.OL", "sourceFetchedAt": FETCHED}]}]},
        "events.json": {"errors": [], "coverage": {}},
    }
    for name, payload in documents.items():
        payload["snapshotId"] = "candidate"
        trust.write_json(path / name, payload)
    return documents


@pytest.mark.parametrize("case", ["stale_fetch", "future_fetch", "unknown_fetch", "future_quote", "future_statement", "missing_company", "peer_mismatch", "mixed_snapshot", "bad_source", "leaked_signal"])
def test_invalid_candidate_blocked(tmp_path, case):
    data = bundle(tmp_path)
    row = data["fundamentals-watchlist.json"]["rows"][0]
    if case in {"stale_fetch", "future_fetch", "unknown_fetch"}:
        row["sourceFetchedAt"] = {"stale_fetch": "2026-09-05T12:00:00Z", "future_fetch": "2026-09-10T12:00:00Z", "unknown_fetch": None}[case]
    elif case == "future_quote":
        row["priceObservedAt"] = "2026-09-10T14:30:00Z"
    elif case == "future_statement":
        row["quarterlyStatements"]["periods"][0]["periodEnd"] = "2026-12-31"
    elif case == "missing_company":
        data["fundamentals-watchlist.json"]["rows"] = []
    elif case == "peer_mismatch":
        data["watchlist-overview.json"]["rows"][0]["peerContext"]["loadedPeerCount"] = 0
    elif case == "mixed_snapshot":
        data["watchlist-overview.json"]["snapshotId"] = "prior-run"
    elif case == "bad_source":
        row["cacheStatus"] = "stale-after-error"
    elif case == "leaked_signal":
        data["technical-indicators-watchlist.json"]["sourceHealth"].update(status="blocked", actionable=False)
    for name, payload in data.items():
        trust.write_json(tmp_path / name, payload)
    result = trust.validate_bundle(tmp_path, ["MOWI.OL"], "candidate", NOW)
    assert result["status"] == "blocked", result
    assert result["issues"]


def test_unknown_primary_and_quote_dates_remain_degraded(tmp_path):
    data = bundle(tmp_path)
    row = data["fundamentals-watchlist.json"]["rows"][0]
    row["priceObservedAt"] = None
    trust.write_json(tmp_path / "fundamentals-watchlist.json", data["fundamentals-watchlist.json"])
    result = trust.validate_bundle(tmp_path, ["MOWI.OL"], "candidate", NOW)
    assert result["status"] == "degraded"
    assert result["source_fetched_at"] == FETCHED
    assert result["source_observation_end"] is None
    assert result["coverage"]["primary_reviewed_periods"] == 0
    assert result["statements"]["filing_publication_dates"] == "unverified"


class HistoryServer:
    BENCHMARK_METRICS = [{"key": "trailingPE"}]

    def __init__(self, path):
        self.path = path
        with self.connect() as con:
            con.execute("create table fundamentals_snapshots(symbol text,payload text,fetched_at_epoch integer,fetched_at text)")

    @contextmanager
    def connect(self):
        con = sqlite3.connect(self.path)
        con.row_factory = sqlite3.Row
        try:
            with con:
                yield con
        finally:
            con.close()


def history_row(fetched, value=12):
    return {"symbol": "MOWI.OL", "fetched_at": fetched,
            "payload": {"symbol": "MOWI.OL", "fetchedAt": fetched, "trailingPE": value}}


def test_history_survives_fresh_builds_and_same_day_is_one_observation(tmp_path):
    public = tmp_path / "data"
    first = HistoryServer(tmp_path / "first.sqlite3")
    rows = [history_row(f"2026-09-08T{hour}:00:00+00:00", int(hour)) for hour in ("08", "09", "10", "11", "12")]
    trust.write_json(public / "fundamentals-history.json", {"schema_version": 1, "rows": rows})
    assert trust.restore_history(first, public, NOW) == 1
    trust.export_history(first, public, NOW)
    second = HistoryServer(tmp_path / "second.sqlite3")
    assert trust.restore_history(second, public, NOW) == 1
    today = history_row(FETCHED, 14)
    with second.connect() as con:
        con.execute("insert into fundamentals_snapshots values(?,?,?,?)", (today["symbol"], json.dumps(today["payload"]), int(NOW.timestamp()), FETCHED))
    result = trust.export_history(second, public, NOW)
    assert [r["date"] for r in result["rows"]] == ["2026-09-08", "2026-09-09"]
    assert result["rows"][0]["payload"]["trailingPE"] == 12


@pytest.mark.parametrize("fetched", [None, "2026-09-09T07:00:00", "2026-09-10T07:00:00Z"])
def test_unknown_or_future_history_rejected(tmp_path, fetched):
    with pytest.raises(ValueError):
        trust.history_rows(HistoryServer(tmp_path / "db"), [history_row(fetched)], NOW)


def test_five_nearby_days_do_not_claim_sufficient_history(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "DB_PATH", tmp_path / "history.sqlite3")
    server.init_db()
    dates = ["2026-06-01T12:00:00Z", *[f"2026-09-0{day}T12:00:00Z" for day in range(1, 6)]]
    with server.connect() as con:
        for index, fetched in enumerate(dates):
            row = history_row(fetched, None if index == 0 else index)
            con.execute("insert into fundamentals_snapshots(symbol,payload,fetched_at_epoch,fetched_at) values(?,?,?,?)",
                        (row["symbol"], json.dumps(row["payload"]), int(trust.timestamp(fetched).timestamp()), fetched))
    history = server.own_history_summary("MOWI.OL")
    metric = next(m for m in history["metrics"] if m["key"] == "trailingPE")
    assert metric["observations"] == 5
    assert metric["spanDays"] == 4
    assert not metric["minimumDataMet"]
    assert history["status"] == "insufficient history"
    assert history["trendCharts"][0]["status"] == "insufficient observations"


def test_history_span_uses_calendar_dates_not_elapsed_whole_days():
    points = [{"fetched_at": fetched, "payload": {"trailingPE": 10}} for fetched in
              ("2026-09-08T23:00:00Z", "2026-09-09T01:00:00Z")]
    chart = server.own_history_chart({"key": "trailingPE", "label": "P/E", "unit": "x"}, points)
    assert chart["spanDays"] == 1


def test_invalid_attempt_retains_good_data_and_history(tmp_path):
    public, candidate = tmp_path / "public" / "data", tmp_path / "candidate"
    bundle(public)
    trust.write_json(public / "fundamentals-history.json", {"schema_version": 1, "rows": []})
    before = {str(p.relative_to(public)): p.read_bytes() for p in public.rglob("*.json")}
    trust.write_json(public.parent / "health.json", {"snapshot_id": "good", "status": "degraded"})
    candidate.mkdir()
    assert not trust.promote(candidate, public, {"snapshot_id": "bad", "status": "blocked"})
    assert before == {str(p.relative_to(public)): p.read_bytes() for p in public.rglob("*.json")}
    assert trust.read_json(public.parent / "health.json")["last_good_snapshot_id"] == "good"


def test_failure_before_collection_creates_public_health(tmp_path, monkeypatch):
    public = tmp_path / "public" / "data"
    monkeypatch.setattr(build, "parse_args", lambda: SimpleNamespace(output_dir=public, input_dir=tmp_path / "missing-inputs"))
    assert build.main() == 1
    assert trust.read_json(public.parent / "health.json")["status"] == "blocked"
    assert not public.exists()


def csv_source(**changes):
    row = {"ticker": "MOWI.OL", "date": "2026-09-08", "snapshot_id": "s1", "data_status": "current",
           "close": 200, "rsi14": 25, "rsi_dir": 1, "macd_hist": 1, "sma50": 190, "adx14": 25, "rsi6": 30,
           "signal": "BUY", "stop_loss_pct": 5, "position_pct": 10,
           "pct_above_sma50": 5.263, "primary_count": 3}
    row.update(changes)
    out = io.StringIO()
    out.write("# oslo-screener schema=oslo_screener.health.v1 snapshot_id=s1 generated_at=2026-09-09T07:00:00Z expected_session=2026-09-08 universe_count=1 status=current\n")
    writer = csv.DictWriter(out, fieldnames=list(row))
    writer.writeheader(); writer.writerow(row)
    return out.getvalue()


@pytest.mark.parametrize("change", [{"date": "2026-09-07"}, {"date": "2026-09-09"}, {"snapshot_id": "other"}, {"close": "NaN"}, {"data_status": "missing"}])
def test_bad_technical_observation_withholds_sizing(change):
    result = server.parse_technical_csv(csv_source(**change), "test.csv", NOW)
    row = result["rows"][0]
    assert result["sourceHealth"]["status"] == "blocked"
    assert row["signal"] == "WITHHELD" and row["positionPct"] is None and row["stopLossPct"] is None


def test_current_completed_technical_observation_passes():
    result = server.parse_technical_csv(csv_source(), "test.csv", NOW)
    assert result["sourceHealth"]["status"] == "current"
    assert result["rows"][0]["signal"] == "BUY"


def test_published_health_hash_mismatch_withholds(monkeypatch):
    csv_text = csv_source()
    response = SimpleNamespace(text=csv_text, content=csv_text.encode(), raise_for_status=lambda: None)
    health_response = SimpleNamespace(raise_for_status=lambda: None, json=lambda: {"snapshot_id": "s1", "artifacts": {"latest.csv": "wrong"}, "status": "current", "actionable": True})
    monkeypatch.setattr(server.requests, "get", lambda url, **kw: health_response if url.endswith("health.json") else response)
    monkeypatch.setattr(server, "TECHNICAL_CACHE", {})
    result = server.fetch_technical_indicators(refresh=True)
    assert result["rows"][0]["signal"] == "WITHHELD"
    assert "hash differs" in result["rows"][0]["withheldReason"]


@pytest.mark.parametrize("published_status", ["current", "blocked"])
def test_verified_csv_requires_published_health_permission(monkeypatch, published_status):
    text = csv_source()
    parse = server.parse_technical_csv
    monkeypatch.setattr(server, "parse_technical_csv", lambda text, url: parse(text, url, NOW))
    response = SimpleNamespace(text=text, content=text.encode(), raise_for_status=lambda: None)
    health = {"snapshot_id": "s1", "artifacts": {"latest.csv": hashlib.sha256(text.encode()).hexdigest()},
              "status": published_status, "actionable": published_status == "current"}
    published = SimpleNamespace(raise_for_status=lambda: None, json=lambda: health)
    monkeypatch.setattr(server.requests, "get", lambda url, **kw: published if url.endswith("health.json") else response)
    monkeypatch.setattr(server, "TECHNICAL_CACHE", {})
    result = server.fetch_technical_indicators(refresh=True)
    assert result["rows"][0]["signal"] == ("BUY" if published_status == "current" else "WITHHELD")


def test_consensus_reenrichment_preserves_retrieval_and_unknown_estimate_date(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "DB_PATH", tmp_path / "db.sqlite3")
    server.init_db()
    payload = {"symbol": "MOWI.OL", "targetMeanPrice": 200, "fetchedAt": "2026-09-01T10:00:00Z", "sourceFetchedAt": "2026-09-01T10:00:00Z"}
    server.record_consensus_source(payload)
    server.record_consensus_source(payload)
    with server.connect() as con:
        row = dict(con.execute("select * from consensus_sources where symbol='MOWI.OL'").fetchone())
    assert row["collected_at"] == payload["sourceFetchedAt"]
    assert row["as_of_date"] == ""


def test_overview_is_emitted_after_peer_collection(tmp_path, monkeypatch):
    peer_loaded = False
    calls = []
    def overview(**kw):
        calls.append(("overview", peer_loaded))
        return {"rows": [{"symbol": "MOWI.OL", "peerContext": {"loadedPeerCount": int(peer_loaded)}}]}
    def benchmark(*args, **kw):
        nonlocal peer_loaded
        peer_loaded = True
        calls.append(("peers", True))
        return {"groups": []}
    fake = SimpleNamespace(watchlist_overview=overview, benchmark_for_symbol=benchmark,
                           screener_alerts=lambda **kw: {}, technical_indicators=lambda **kw: {},
                           event_monitoring_payload=lambda **kw: {}, source_notes=lambda: {})
    monkeypatch.setattr(build, "watchlist_payload", lambda *a: {})
    monkeypatch.setattr(build, "fundamentals_payload", lambda *a, **kw: {})
    monkeypatch.setattr(build, "consensus_payload", lambda *a: {})
    build.build_static_outputs(fake, {"watchlist": {"watchlist": "Core", "items": [{"symbol": "MOWI.OL"}]}}, tmp_path, True, False)
    assert calls == [("overview", False), ("peers", True), ("overview", True)]
    assert trust.read_json(tmp_path / "watchlist-overview.json")["rows"][0]["peerContext"]["loadedPeerCount"] == 1


def test_empty_peer_payload_is_not_loaded_coverage(monkeypatch):
    group = {"group_key": "seafood", "name": "Seafood", "status": "trusted"}
    items = [{"symbol": "MOWI.OL", "role": "focus company", "market": "Oslo"},
             {"symbol": "GOOD.OL", "role": "Oslo peer", "market": "Oslo"},
             {"symbol": "EMPTY.OL", "role": "Oslo peer", "market": "Oslo"}]
    payloads = {i["symbol"]: {"symbol": i["symbol"], "trailingPE": None if i["symbol"] == "EMPTY.OL" else 10} for i in items}
    monkeypatch.setattr(server, "peer_groups_for_symbol", lambda s: [group])
    monkeypatch.setattr(server, "peer_group_items", lambda k: items)
    monkeypatch.setattr(server, "cached_payload_if_present", lambda s: payloads[s])
    monkeypatch.setattr(server, "cached_fundamental", lambda s, **kw: payloads[s])
    monkeypatch.setattr(server, "own_history_summary", lambda s: {})
    monkeypatch.setattr(server, "sector_context", lambda *a: {})
    monkeypatch.setattr(server, "minimum_data_assessment", lambda *a: {})
    overview = server.peer_context_summary("MOWI.OL", payloads["MOWI.OL"])
    detail = server.benchmark_for_symbol("MOWI.OL")["groups"][0]
    assert overview["loadedPeerCount"] == 1
    assert [r["symbol"] for r in detail["items"]] == ["MOWI.OL", "GOOD.OL"]
    assert detail["errors"][0]["symbol"] == "EMPTY.OL"
