"""Static publication checks and durable, date-keyed retrieval history.

Retrieval dates are not estimate dates, filing dates, or historical backtest
observations. A failed candidate only updates public health; its data is retained
in staging and the prior published bundle remains intact.
"""
from __future__ import annotations

import json
import math
import os
import shutil
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path


def timestamp(value):
    try:
        value = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return value.astimezone(timezone.utc) if value.tzinfo else None
    except (TypeError, ValueError):
        return None


def read_json(path):
    return json.loads(Path(path).read_text())


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n")
    os.replace(temporary, path)


def history_rows(server, rows, now=None):
    now = now or datetime.now(timezone.utc)
    keys = {m["key"] for m in server.BENCHMARK_METRICS} | {
        "symbol", "price", "currency", "financialCurrency", "source", "fetchedAt",
        "sourceFetchedAt", "priceObservedAt", "priceObservationStatus", "priceSourceField",
    }
    by_day = {}
    for row in sorted(rows, key=lambda r: r.get("fetched_at") or ""):
        observed = timestamp(row.get("fetched_at"))
        if not observed or observed > now:
            raise ValueError("History contains unknown/future retrieval date")
        symbol = row["symbol"]
        payload = row["payload"]
        if isinstance(payload, str):
            payload = json.loads(payload)
        if payload.get("symbol") != symbol or timestamp(payload.get("fetchedAt")) != observed:
            raise ValueError("History row identity/timestamp differs from its payload")
        day = observed.date().isoformat()
        if row.get("date", day) != day:
            raise ValueError("History date key differs from retrieval date")
        by_day[(symbol, day)] = {"symbol": symbol, "date": day,
                                "fetched_at": observed.isoformat(),
                                "payload": {k: v for k, v in payload.items() if k in keys}}
    return sorted(by_day.values(), key=lambda r: (r["symbol"], r["date"]))


def restore_history(server, published_dir, now=None):
    path = Path(published_dir) / "fundamentals-history.json"
    if path.exists():
        document = read_json(path)
        if document.get("schema_version") != 1:
            raise ValueError("Unrecognized daily history schema")
        rows = document["rows"]
    else:
        # Bootstrap only the one genuinely stored previous retrieval. Never
        # backfill daily history from repeated builds or present-day prices.
        previous = Path(published_dir) / "fundamentals-watchlist.json"
        rows = [{"symbol": r["symbol"], "fetched_at": r.get("fetchedAt"), "payload": r}
                for r in read_json(previous).get("rows", [])] if previous.exists() else []
    rows = history_rows(server, rows, now)
    with server.connect() as con:
        for row in rows:
            con.execute("delete from fundamentals_snapshots where symbol=? and substr(fetched_at,1,10)=?",
                        (row["symbol"], row["date"]))
            con.execute("insert into fundamentals_snapshots(symbol,payload,fetched_at_epoch,fetched_at) values (?,?,?,?)",
                        (row["symbol"], json.dumps(row["payload"], allow_nan=False),
                         int(timestamp(row["fetched_at"]).timestamp()), row["fetched_at"]))
    return len(rows)


def export_history(server, output_dir, now=None):
    with server.connect() as con:
        rows = [dict(r) for r in con.execute("select symbol,payload,fetched_at from fundamentals_snapshots")]
    rows = history_rows(server, rows, now)
    document = {"schema_version": 1, "date_basis": "UTC source retrieval date; latest retrieval per symbol/day",
                "limitations": "Prospective provider snapshots, not point-in-time backtest data. Estimate/filing dates remain separate.",
                "rows": rows}
    write_json(Path(output_dir) / "fundamentals-history.json", document)
    return document


def validate_bundle(output_dir, symbols, snapshot_id=None, now=None):
    now = now or datetime.now(timezone.utc)
    output_dir = Path(output_dir)
    errors, issues, observations, fetches, latest_periods = [], [], [], [], []
    expected = set(symbols)
    documents = {}
    for filename in ("fundamentals-watchlist.json", "watchlist-overview.json", "technical-indicators-watchlist.json"):
        document = read_json(output_dir / filename)
        if not snapshot_id or document.get("snapshotId") != snapshot_id:
            errors.append(f"{filename}: publication snapshot mismatch")
        documents[filename] = document
        rows = document.get("rows", [])
        identities = [r.get("symbol") for r in rows]
        if set(identities) != expected or len(identities) != len(expected):
            errors.append(f"{filename}: missing/duplicate/unexpected watchlist rows")
    fundamentals = documents["fundamentals-watchlist.json"]
    overview = documents["watchlist-overview.json"]
    technical = documents["technical-indicators-watchlist.json"]
    if fundamentals.get("errors"):
        errors.append("Fundamental source collection failed")
    missing_quotes = stale_quotes = invalid_quotes = missing_periods = aged_periods = period_count = reviewed = received = 0
    technical_health = technical.get("sourceHealth") or {}
    expected_session = technical_health.get("expected_session")
    for row in fundamentals.get("rows", []):
        symbol = row["symbol"]
        fetched = timestamp(row.get("sourceFetchedAt"))
        if not fetched or not timedelta(0) <= now - fetched <= timedelta(hours=24):
            errors.append(f"{symbol}: unknown/stale/future source retrieval time")
        else:
            fetches.append(fetched.isoformat())
        if row.get("sourceRefreshError") or row.get("cacheStatus") == "stale-after-error":
            errors.append(f"{symbol}: source refresh failed; retained cached data")
        price = row.get("price")
        if not isinstance(price, (int, float)) or not math.isfinite(price) or price <= 0:
            errors.append(f"{symbol}: missing/invalid price")
        else:
            received += 1
        quote = timestamp(row.get("priceObservedAt"))
        if not quote:
            missing_quotes += 1
        elif quote > now:
            errors.append(f"{symbol}: future quote observation")
            invalid_quotes += 1
        else:
            observations.append(quote.date().isoformat())
            if expected_session and quote.date().isoformat() < expected_session:
                stale_quotes += 1
        statements = row.get("quarterlyStatements") or {}
        periods = statements.get("periods") or []
        dates = []
        for period in periods:
            try:
                end = date.fromisoformat(period["periodEnd"])
                if end > now.date():
                    raise ValueError("future")
                dates.append(end)
            except (KeyError, TypeError, ValueError):
                errors.append(f"{symbol}: invalid/future statement period")
        period_count += len(periods)
        reviewed += sum(bool(p.get("primaryReportReview", {}).get("isPrimaryReviewed")) for p in periods)
        if dates:
            latest = max(dates)
            latest_periods.append(latest.isoformat())
            if (now.date() - latest).days > 180:
                aged_periods += 1
        else:
            missing_periods += 1
    missing_peers = set()
    for row in overview.get("rows", []):
        symbol = row["symbol"]
        benchmark = read_json(output_dir / "benchmarks" / f"{symbol}.json")
        if benchmark.get("snapshotId") != snapshot_id:
            errors.append(f"{symbol}: benchmark snapshot mismatch")
        groups = benchmark.get("groups") or []
        context = row.get("peerContext") or {}
        if groups:
            peers = {p["symbol"] for p in groups[0].get("items", []) if p["symbol"] != symbol}
            if context.get("loadedPeerCount") != len(peers) or context.get("groupName") != groups[0].get("name"):
                errors.append(f"{symbol}: overview and benchmark peer coverage disagree")
            if any(g.get("errors") for g in groups):
                issues.append(f"{symbol}: peer source coverage incomplete")
                missing_peers.update(e.get("symbol") for g in groups for e in g.get("errors", []) if e.get("symbol"))
            for group in groups:
                for peer in group.get("items", []):
                    fetched = timestamp(peer.get("sourceFetchedAt"))
                    if not fetched or not timedelta(0) <= now - fetched <= timedelta(hours=24):
                        issues.append(f"{peer['symbol']}: peer source retrieval unknown/stale/future")
    if missing_quotes:
        issues.append(f"{missing_quotes}/{len(expected)} quote observation timestamps unverified")
    if stale_quotes:
        issues.append(f"{stale_quotes}/{len(expected)} quote observations predate expected completed session")
    if missing_periods or aged_periods:
        issues.append(f"Statements: {missing_periods} companies missing, {aged_periods} latest periods older than 180 days")
    if reviewed < period_count:
        issues.append(f"Primary filing verification: {reviewed}/{period_count} statement periods reviewed; filing publication dates unverified")
    if technical_health.get("status") not in {"current", "degraded"} or not technical_health.get("actionable"):
        issues.append("Technical source blocked/unverified; signal and sizing labels withheld")
        if any(r.get("signal") not in {"WITHHELD", "MISSING"} for r in technical.get("rows", [])):
            errors.append("Blocked technical source still contains usable signal labels")
    events = read_json(output_dir / "events.json")
    if events.get("errors") or events.get("coverage", {}).get("newswebFetch", {}).get("errorSymbols"):
        issues.append("NewsWeb source coverage incomplete; absence of events is not verified")
    return {"schema": "oslo_workspace.health.v1", "snapshot_id": snapshot_id or uuid.uuid4().hex,
            "generated_at": now.isoformat(), "evaluated_at": now.isoformat(),
            "status": "blocked" if errors else "degraded" if issues else "current",
            "source_fetched_at": min(fetches) if fetches else None,
            "source_observation_start": min(observations) if observations else None,
            "source_observation_end": max(observations) if observations else None,
            "market_data_as_of": min(observations) if observations else None,
            "expected_session": expected_session, "valid_until": technical_health.get("valid_until"),
            "coverage": {"expected": len(expected), "received": received, "refreshed": len(fetches),
                         "current": max(0, received - missing_quotes - stale_quotes - invalid_quotes),
                         "missing": len(expected) - received,
                         "missing_quote_dates": missing_quotes, "stale_quote_dates": stale_quotes,
                         "invalid_quote_dates": invalid_quotes,
                         "statement_periods": period_count, "primary_reviewed_periods": reviewed,
                         "missing_statements": missing_periods, "aged_statements": aged_periods,
                         "missing_peer_companies": len(missing_peers),
                         "technical_current": technical.get("coverage", {}).get("coveredCount", 0),
                         "technical_missing": technical.get("coverage", {}).get("missingCount", len(expected)),
                         "technical_withheld": technical.get("coverage", {}).get("withheldCount", 0)},
            "statements": {"latest_period_start": min(latest_periods) if latest_periods else None,
                           "latest_period_end": max(latest_periods) if latest_periods else None,
                           "filing_publication_dates": "unverified"},
            "missing_peers": sorted(missing_peers),
            "issues": errors + issues, "reasons": errors + issues,
            "sources": {"technical": technical_health, "news": events.get("coverage", {})}}


def promote(candidate_dir, published_dir, health):
    candidate_dir, published_dir = Path(candidate_dir), Path(published_dir)
    health_path = published_dir.parent / "health.json"
    try:
        previous = read_json(health_path)
    except (OSError, ValueError):
        previous = {}
    if health.get("status") not in {"current", "degraded"}:
        health["status"] = "blocked"
        health.update(published_content_retained=True,
                      last_good_snapshot_id=previous.get("last_good_snapshot_id") or previous.get("snapshot_id"))
        write_json(health_path, health)
        return False
    # Directory promotion is reversible locally; Git publishes one complete
    # bundle commit. Failed builders must stage only health.json in Actions.
    replacement = published_dir.with_name(published_dir.name + ".candidate")
    backup = published_dir.with_name(published_dir.name + ".previous")
    shutil.copytree(candidate_dir, replacement)
    had_previous = published_dir.exists()
    try:
        if had_previous:
            os.replace(published_dir, backup)
        os.replace(replacement, published_dir)
        health.update(published_content_retained=False, last_good_snapshot_id=health["snapshot_id"])
        write_json(health_path, health)
    except Exception:
        if backup.exists():
            if published_dir.exists():
                shutil.rmtree(published_dir)
            os.replace(backup, published_dir)
        elif not had_previous and published_dir.exists():
            shutil.rmtree(published_dir)
        raise
    finally:
        if replacement.exists():
            shutil.rmtree(replacement)
    if backup.exists():
        shutil.rmtree(backup)
    return True
