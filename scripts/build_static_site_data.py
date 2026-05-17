#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import time
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
INPUT_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "docs" / "data"
DOCS_DIR = ROOT / "docs"
STATIC_DIR = ROOT / "app" / "static"
REPO_URL = "https://github.com/keresell-coder/oslo-market-workspace"
WATCHLIST_SOURCE_URL = f"{REPO_URL}/edit/main/data/watchlist.yml"
WORKFLOW_URL = f"{REPO_URL}/actions/workflows/static-data.yml"


class SchemaError(ValueError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_yaml_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SchemaError(f"{path.relative_to(ROOT)} is missing")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise SchemaError(f"{path.relative_to(ROOT)} must be a YAML mapping")
    return data


def validate_keys(label: str, item: dict[str, Any], required: set[str], allowed: set[str]) -> None:
    keys = set(item)
    missing = required - keys
    extra = keys - allowed
    if missing:
        raise SchemaError(f"{label} missing required keys: {', '.join(sorted(missing))}")
    if extra:
        raise SchemaError(f"{label} has unsupported keys: {', '.join(sorted(extra))}")


def validate_str(label: str, value: Any, *, required: bool = True) -> str:
    if value is None:
        if required:
            raise SchemaError(f"{label} is required")
        return ""
    if not isinstance(value, str):
        raise SchemaError(f"{label} must be a string")
    if required and not value.strip():
        raise SchemaError(f"{label} cannot be blank")
    return value.strip()


def validate_number(label: str, value: Any) -> float | None:
    if value in (None, ""):
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SchemaError(f"{label} must be a number or null")
    return float(value)


def validate_row_list(root: dict[str, Any], key: str, filename: str) -> list[dict[str, Any]]:
    rows = root.get(key, [])
    if not isinstance(rows, list):
        raise SchemaError(f"{filename}:{key} must be a list")
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise SchemaError(f"{filename}:{key}[{index}] must be a mapping")
    return rows


def validate_watchlist(data: dict[str, Any]) -> dict[str, Any]:
    validate_keys("watchlist.yml", data, {"watchlist", "items"}, {"watchlist", "items", "notes"})
    watchlist = validate_str("watchlist.yml:watchlist", data["watchlist"])
    items = validate_row_list(data, "items", "watchlist.yml")
    allowed = {"symbol", "name", "sector", "industry", "note"}
    seen: set[str] = set()
    normalized = []
    for index, item in enumerate(items, start=1):
        validate_keys(f"watchlist.yml:items[{index}]", item, {"symbol"}, allowed)
        symbol = validate_str(f"watchlist.yml:items[{index}].symbol", item["symbol"]).upper()
        if "." not in symbol:
            symbol = f"{symbol}.OL"
        if symbol in seen:
            raise SchemaError(f"watchlist.yml duplicates symbol {symbol}")
        seen.add(symbol)
        normalized.append(
            {
                "symbol": symbol,
                "name": validate_str(f"watchlist.yml:items[{index}].name", item.get("name", ""), required=False),
                "sector": validate_str(f"watchlist.yml:items[{index}].sector", item.get("sector", ""), required=False),
                "industry": validate_str(f"watchlist.yml:items[{index}].industry", item.get("industry", ""), required=False),
                "note": validate_str(f"watchlist.yml:items[{index}].note", item.get("note", ""), required=False),
            }
        )
    if not normalized:
        raise SchemaError("watchlist.yml must contain at least one item")
    return {"watchlist": watchlist, "items": normalized}


def validate_manual_consensus(data: dict[str, Any]) -> list[dict[str, Any]]:
    validate_keys("manual_consensus.yml", data, set(), {"rows", "notes"})
    rows = validate_row_list(data, "rows", "manual_consensus.yml")
    allowed = {
        "symbol",
        "source",
        "source_type",
        "review_status",
        "target_mean",
        "target_high",
        "target_low",
        "analyst_count",
        "recommendation",
        "recommendation_score",
        "target_currency",
        "as_of_date",
        "source_url",
        "confidence",
        "method_note",
        "limitation_note",
        "collected_at",
    }
    normalized = []
    seen: set[tuple[str, str]] = set()
    for index, row in enumerate(rows, start=1):
        validate_keys(f"manual_consensus.yml:rows[{index}]", row, {"symbol", "source"}, allowed)
        symbol = validate_str(f"manual_consensus.yml:rows[{index}].symbol", row["symbol"]).upper()
        source = validate_str(f"manual_consensus.yml:rows[{index}].source", row["source"])
        key = (symbol, source)
        if key in seen:
            raise SchemaError(f"manual_consensus.yml duplicates {symbol} / {source}")
        seen.add(key)
        normalized.append(
            {
                "symbol": symbol,
                "source": source,
                "source_type": validate_str(f"manual_consensus.yml:rows[{index}].source_type", row.get("source_type", "manual-source"), required=False) or "manual-source",
                "review_status": validate_str(f"manual_consensus.yml:rows[{index}].review_status", row.get("review_status", "draft"), required=False) or "draft",
                "target_mean": validate_number(f"manual_consensus.yml:rows[{index}].target_mean", row.get("target_mean")),
                "target_high": validate_number(f"manual_consensus.yml:rows[{index}].target_high", row.get("target_high")),
                "target_low": validate_number(f"manual_consensus.yml:rows[{index}].target_low", row.get("target_low")),
                "analyst_count": validate_number(f"manual_consensus.yml:rows[{index}].analyst_count", row.get("analyst_count")),
                "recommendation": validate_str(f"manual_consensus.yml:rows[{index}].recommendation", row.get("recommendation", ""), required=False),
                "recommendation_score": validate_number(f"manual_consensus.yml:rows[{index}].recommendation_score", row.get("recommendation_score")),
                "target_currency": validate_str(f"manual_consensus.yml:rows[{index}].target_currency", row.get("target_currency", ""), required=False),
                "as_of_date": validate_str(f"manual_consensus.yml:rows[{index}].as_of_date", row.get("as_of_date", ""), required=False),
                "source_url": validate_str(f"manual_consensus.yml:rows[{index}].source_url", row.get("source_url", ""), required=False),
                "confidence": validate_str(f"manual_consensus.yml:rows[{index}].confidence", row.get("confidence", "manual"), required=False) or "manual",
                "method_note": validate_str(f"manual_consensus.yml:rows[{index}].method_note", row.get("method_note", ""), required=False),
                "limitation_note": validate_str(f"manual_consensus.yml:rows[{index}].limitation_note", row.get("limitation_note", ""), required=False),
                "collected_at": validate_str(f"manual_consensus.yml:rows[{index}].collected_at", row.get("collected_at", ""), required=False),
            }
        )
    return normalized


def validate_peer_groups(data: dict[str, Any]) -> list[dict[str, Any]]:
    validate_keys("peer_groups.yml", data, set(), {"groups", "notes"})
    groups = validate_row_list(data, "groups", "peer_groups.yml")
    group_allowed = {"group_key", "name", "description", "status", "curator_note", "source", "items"}
    item_allowed = {"symbol", "role", "market", "note"}
    seen_groups: set[str] = set()
    normalized = []
    for group_index, group in enumerate(groups, start=1):
        validate_keys(f"peer_groups.yml:groups[{group_index}]", group, {"group_key", "name", "items"}, group_allowed)
        group_key = validate_str(f"peer_groups.yml:groups[{group_index}].group_key", group["group_key"])
        if group_key in seen_groups:
            raise SchemaError(f"peer_groups.yml duplicates group {group_key}")
        seen_groups.add(group_key)
        items = group.get("items", [])
        if not isinstance(items, list):
            raise SchemaError(f"peer_groups.yml:groups[{group_index}].items must be a list")
        normalized_items = []
        seen_items: set[str] = set()
        for item_index, item in enumerate(items, start=1):
            if not isinstance(item, dict):
                raise SchemaError(f"peer_groups.yml:groups[{group_index}].items[{item_index}] must be a mapping")
            validate_keys(
                f"peer_groups.yml:groups[{group_index}].items[{item_index}]",
                item,
                {"symbol", "role"},
                item_allowed,
            )
            symbol = validate_str(f"peer_groups.yml:groups[{group_index}].items[{item_index}].symbol", item["symbol"]).upper()
            if symbol in seen_items:
                raise SchemaError(f"peer_groups.yml group {group_key} duplicates item {symbol}")
            seen_items.add(symbol)
            normalized_items.append(
                {
                    "symbol": symbol,
                    "role": validate_str(f"peer_groups.yml:groups[{group_index}].items[{item_index}].role", item["role"]),
                    "market": validate_str(f"peer_groups.yml:groups[{group_index}].items[{item_index}].market", item.get("market", ""), required=False),
                    "note": validate_str(f"peer_groups.yml:groups[{group_index}].items[{item_index}].note", item.get("note", ""), required=False),
                }
            )
        if not normalized_items:
            raise SchemaError(f"peer_groups.yml group {group_key} must have at least one item")
        normalized.append(
            {
                "group_key": group_key,
                "name": validate_str(f"peer_groups.yml:groups[{group_index}].name", group["name"]),
                "description": validate_str(f"peer_groups.yml:groups[{group_index}].description", group.get("description", ""), required=False),
                "status": validate_str(f"peer_groups.yml:groups[{group_index}].status", group.get("status", "draft"), required=False) or "draft",
                "curator_note": validate_str(f"peer_groups.yml:groups[{group_index}].curator_note", group.get("curator_note", ""), required=False),
                "source": validate_str(f"peer_groups.yml:groups[{group_index}].source", group.get("source", "manual"), required=False) or "manual",
                "items": normalized_items,
            }
        )
    return normalized


def validate_sector_kpis(data: dict[str, Any]) -> list[dict[str, Any]]:
    validate_keys("sector_kpis.yml", data, set(), {"rows", "notes"})
    rows = validate_row_list(data, "rows", "sector_kpis.yml")
    allowed = {"symbol", "kpi_key", "label", "value", "unit", "period", "status", "input_type", "source_name", "source_url", "note"}
    normalized = []
    seen: set[tuple[str, str]] = set()
    for index, row in enumerate(rows, start=1):
        validate_keys(f"sector_kpis.yml:rows[{index}]", row, {"symbol", "kpi_key", "label"}, allowed)
        symbol = validate_str(f"sector_kpis.yml:rows[{index}].symbol", row["symbol"]).upper()
        kpi_key = validate_str(f"sector_kpis.yml:rows[{index}].kpi_key", row["kpi_key"])
        key = (symbol, kpi_key)
        if key in seen:
            raise SchemaError(f"sector_kpis.yml duplicates {symbol} / {kpi_key}")
        seen.add(key)
        normalized.append(
            {
                "symbol": symbol,
                "kpi_key": kpi_key,
                "label": validate_str(f"sector_kpis.yml:rows[{index}].label", row["label"]),
                "value": validate_number(f"sector_kpis.yml:rows[{index}].value", row.get("value")),
                "unit": validate_str(f"sector_kpis.yml:rows[{index}].unit", row.get("unit", ""), required=False),
                "period": validate_str(f"sector_kpis.yml:rows[{index}].period", row.get("period", ""), required=False),
                "status": validate_str(f"sector_kpis.yml:rows[{index}].status", row.get("status", "draft"), required=False) or "draft",
                "input_type": validate_str(f"sector_kpis.yml:rows[{index}].input_type", row.get("input_type", "manual"), required=False) or "manual",
                "source_name": validate_str(f"sector_kpis.yml:rows[{index}].source_name", row.get("source_name", ""), required=False),
                "source_url": validate_str(f"sector_kpis.yml:rows[{index}].source_url", row.get("source_url", ""), required=False),
                "note": validate_str(f"sector_kpis.yml:rows[{index}].note", row.get("note", ""), required=False),
            }
        )
    return normalized


def validate_manual_events(data: dict[str, Any]) -> list[dict[str, Any]]:
    validate_keys("manual_events.yml", data, set(), {"rows", "notes"})
    rows = validate_row_list(data, "rows", "manual_events.yml")
    allowed = {
        "symbol",
        "title",
        "category",
        "importance",
        "source",
        "source_type",
        "review_status",
        "confidence",
        "url",
        "note",
        "published_at",
        "limitation_note",
    }
    normalized = []
    for index, row in enumerate(rows, start=1):
        validate_keys(f"manual_events.yml:rows[{index}]", row, {"symbol", "title"}, allowed)
        normalized.append(
            {
                "symbol": validate_str(f"manual_events.yml:rows[{index}].symbol", row["symbol"]).upper(),
                "title": validate_str(f"manual_events.yml:rows[{index}].title", row["title"]),
                "category": validate_str(f"manual_events.yml:rows[{index}].category", row.get("category", "corporate-action"), required=False) or "corporate-action",
                "importance": validate_str(f"manual_events.yml:rows[{index}].importance", row.get("importance", "normal"), required=False) or "normal",
                "source": validate_str(f"manual_events.yml:rows[{index}].source", row.get("source", "manual"), required=False) or "manual",
                "source_type": validate_str(f"manual_events.yml:rows[{index}].source_type", row.get("source_type", "manual-source"), required=False) or "manual-source",
                "review_status": validate_str(f"manual_events.yml:rows[{index}].review_status", row.get("review_status", "draft"), required=False) or "draft",
                "confidence": validate_str(f"manual_events.yml:rows[{index}].confidence", row.get("confidence", "manual"), required=False) or "manual",
                "url": validate_str(f"manual_events.yml:rows[{index}].url", row.get("url", ""), required=False),
                "note": validate_str(f"manual_events.yml:rows[{index}].note", row.get("note", ""), required=False),
                "published_at": validate_str(f"manual_events.yml:rows[{index}].published_at", row.get("published_at", ""), required=False),
                "limitation_note": validate_str(f"manual_events.yml:rows[{index}].limitation_note", row.get("limitation_note", ""), required=False),
            }
        )
    return normalized


def validate_quarterly_reviews(data: dict[str, Any]) -> list[dict[str, Any]]:
    validate_keys("quarterly_statement_reviews.yml", data, set(), {"rows", "notes"})
    rows = validate_row_list(data, "rows", "quarterly_statement_reviews.yml")
    allowed = {
        "symbol",
        "period_end",
        "review_status",
        "source_name",
        "source_url",
        "report_period",
        "reviewer_note",
        "limitation_note",
        "reviewed_at",
    }
    normalized = []
    seen: set[tuple[str, str]] = set()
    for index, row in enumerate(rows, start=1):
        validate_keys(f"quarterly_statement_reviews.yml:rows[{index}]", row, {"symbol", "period_end"}, allowed)
        symbol = validate_str(f"quarterly_statement_reviews.yml:rows[{index}].symbol", row["symbol"]).upper()
        period_end = validate_str(f"quarterly_statement_reviews.yml:rows[{index}].period_end", row["period_end"])
        key = (symbol, period_end)
        if key in seen:
            raise SchemaError(f"quarterly_statement_reviews.yml duplicates {symbol} / {period_end}")
        seen.add(key)
        normalized.append(
            {
                "symbol": symbol,
                "period_end": period_end,
                "review_status": validate_str(f"quarterly_statement_reviews.yml:rows[{index}].review_status", row.get("review_status", "unverified"), required=False) or "unverified",
                "source_name": validate_str(f"quarterly_statement_reviews.yml:rows[{index}].source_name", row.get("source_name", ""), required=False),
                "source_url": validate_str(f"quarterly_statement_reviews.yml:rows[{index}].source_url", row.get("source_url", ""), required=False),
                "report_period": validate_str(f"quarterly_statement_reviews.yml:rows[{index}].report_period", row.get("report_period", ""), required=False),
                "reviewer_note": validate_str(f"quarterly_statement_reviews.yml:rows[{index}].reviewer_note", row.get("reviewer_note", ""), required=False),
                "limitation_note": validate_str(f"quarterly_statement_reviews.yml:rows[{index}].limitation_note", row.get("limitation_note", ""), required=False),
                "reviewed_at": validate_str(f"quarterly_statement_reviews.yml:rows[{index}].reviewed_at", row.get("reviewed_at", ""), required=False),
            }
        )
    return normalized


def load_inputs(input_dir: Path) -> dict[str, Any]:
    watchlist = validate_watchlist(load_yaml_file(input_dir / "watchlist.yml"))
    return {
        "watchlist": watchlist,
        "manual_consensus": validate_manual_consensus(load_yaml_file(input_dir / "manual_consensus.yml")),
        "peer_groups": validate_peer_groups(load_yaml_file(input_dir / "peer_groups.yml")),
        "sector_kpis": validate_sector_kpis(load_yaml_file(input_dir / "sector_kpis.yml")),
        "manual_events": validate_manual_events(load_yaml_file(input_dir / "manual_events.yml")),
        "quarterly_reviews": validate_quarterly_reviews(load_yaml_file(input_dir / "quarterly_statement_reviews.yml")),
    }


def copy_cache_tables(source_db: Path, target_db: Path) -> None:
    if not source_db.exists():
        return
    with sqlite3.connect(source_db) as source, sqlite3.connect(target_db) as target:
        target.row_factory = sqlite3.Row
        source.row_factory = sqlite3.Row
        for table in ("fundamentals_cache", "fundamentals_snapshots"):
            columns = [row["name"] for row in target.execute(f"pragma table_info({table})").fetchall()]
            if not columns:
                continue
            placeholders = ", ".join("?" for _ in columns)
            column_sql = ", ".join(columns)
            target.execute(f"delete from {table}")
            for row in source.execute(f"select {column_sql} from {table}").fetchall():
                target.execute(f"insert into {table} ({column_sql}) values ({placeholders})", [row[col] for col in columns])
        consensus_columns = [
            row["name"]
            for row in target.execute("pragma table_info(consensus_sources)").fetchall()
        ]
        if consensus_columns:
            column_sql = ", ".join(consensus_columns)
            placeholders = ", ".join("?" for _ in consensus_columns)
            for row in source.execute(
                f"select {column_sql} from consensus_sources where source_type = 'provider-row'"
            ).fetchall():
                target.execute(
                    f"insert or replace into consensus_sources ({column_sql}) values ({placeholders})",
                    [row[col] for col in consensus_columns],
                )


def import_app_server(db_path: Path):
    os.environ["OSLO_APP_DB_PATH"] = str(db_path)
    sys.path.insert(0, str(ROOT))
    from app import server  # pylint: disable=import-outside-toplevel

    server.DB_PATH = db_path
    return server


def install_inputs(server, inputs: dict[str, Any]) -> None:
    now = utc_now()
    now_epoch = int(time.time())
    watchlist = inputs["watchlist"]
    with server.connect() as con:
        con.execute("delete from watchlist_items")
        con.execute("delete from watchlists")
        con.execute("delete from peer_group_items")
        con.execute("delete from peer_groups")
        con.execute("delete from sector_kpi_inputs")
        con.execute("delete from significant_events")
        con.execute("delete from quarterly_statement_reviews")
        con.execute("delete from consensus_sources where source_type != 'provider-row'")

        con.execute("insert into watchlists(name, created_at) values (?, ?)", (watchlist["watchlist"], now))
        for item in watchlist["items"]:
            con.execute(
                """
                insert into tickers(symbol, name, exchange, sector, industry, source, created_at)
                values (?, ?, ?, ?, ?, ?, ?)
                on conflict(symbol) do update set
                    name = coalesce(nullif(excluded.name, ''), tickers.name),
                    sector = coalesce(nullif(excluded.sector, ''), tickers.sector),
                    industry = coalesce(nullif(excluded.industry, ''), tickers.industry)
                """,
                (
                    item["symbol"],
                    item["name"] or item["symbol"].replace(".OL", ""),
                    "Oslo Bors" if item["symbol"].endswith(".OL") else "International",
                    item["sector"],
                    item["industry"],
                    "repo data/watchlist.yml",
                    now,
                ),
            )
            con.execute(
                """
                insert into watchlist_items(watchlist_name, symbol, note, created_at)
                values (?, ?, ?, ?)
                """,
                (watchlist["watchlist"], item["symbol"], item["note"], now),
            )

        for group in inputs["peer_groups"]:
            con.execute(
                """
                insert into peer_groups(group_key, name, description, status, curator_note, source, created_at, updated_at)
                values (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    group["group_key"],
                    group["name"],
                    group["description"],
                    server.normalize_peer_status(group["status"]),
                    group["curator_note"],
                    group["source"],
                    now,
                    now,
                ),
            )
            for item in group["items"]:
                normalized_symbol = server.normalize_peer_symbol(item["symbol"], item["role"], item["market"])
                con.execute(
                    """
                    insert into tickers(symbol, name, exchange, source, created_at)
                    values (?, ?, ?, ?, ?)
                    on conflict(symbol) do nothing
                    """,
                    (
                        normalized_symbol,
                        normalized_symbol.replace(".OL", ""),
                        "Oslo Bors" if normalized_symbol.endswith(".OL") else "International",
                        "repo data/peer_groups.yml",
                        now,
                    ),
                )
                con.execute(
                    """
                    insert into peer_group_items(group_key, symbol, role, market, note, source, created_at, updated_at)
                    values (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        group["group_key"],
                        normalized_symbol,
                        server.normalize_peer_role(item["role"], item["market"]),
                        item["market"],
                        item["note"],
                        group["source"],
                        now,
                        now,
                    ),
                )

        for row in inputs["manual_consensus"]:
            collected_at = row["collected_at"] or now
            con.execute(
                """
                insert or replace into consensus_sources(
                    symbol, source, source_type, review_status, target_mean, target_high, target_low,
                    analyst_count, recommendation, recommendation_score, target_currency, as_of_date,
                    source_url, confidence, method_note, limitation_note, collected_at_epoch, collected_at
                ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row["symbol"],
                    row["source"],
                    row["source_type"],
                    row["review_status"],
                    row["target_mean"],
                    row["target_high"],
                    row["target_low"],
                    row["analyst_count"],
                    row["recommendation"],
                    row["recommendation_score"],
                    row["target_currency"],
                    row["as_of_date"],
                    row["source_url"],
                    row["confidence"],
                    row["method_note"],
                    row["limitation_note"],
                    now_epoch,
                    collected_at,
                ),
            )

        for row in inputs["sector_kpis"]:
            con.execute(
                """
                insert into sector_kpi_inputs(
                    symbol, kpi_key, label, value, unit, period, status, input_type,
                    source_name, source_url, note, updated_at
                ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row["symbol"],
                    row["kpi_key"],
                    row["label"],
                    row["value"],
                    row["unit"],
                    row["period"],
                    server.normalize_sector_kpi_status(row["status"]),
                    server.normalize_sector_kpi_input_type(row["input_type"]),
                    row["source_name"],
                    row["source_url"],
                    row["note"],
                    now,
                ),
            )

        for row in inputs["manual_events"]:
            con.execute(
                """
                insert into significant_events(
                    symbol, title, category, importance, source, url, note, published_at,
                    created_at_epoch, created_at, source_type, review_status, confidence, limitation_note
                ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row["symbol"],
                    row["title"],
                    server.normalize_event_category(row["category"]),
                    row["importance"],
                    row["source"],
                    row["url"],
                    row["note"],
                    row["published_at"],
                    now_epoch,
                    now,
                    row["source_type"],
                    row["review_status"],
                    row["confidence"],
                    row["limitation_note"],
                ),
            )

        for row in inputs["quarterly_reviews"]:
            con.execute(
                """
                insert into quarterly_statement_reviews(
                    symbol, period_end, review_status, source_name, source_url, report_period,
                    reviewer_note, limitation_note, reviewed_at, updated_at
                ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row["symbol"],
                    row["period_end"],
                    row["review_status"],
                    row["source_name"],
                    row["source_url"],
                    row["report_period"],
                    row["reviewer_note"],
                    row["limitation_note"],
                    row["reviewed_at"],
                    now,
                ),
            )


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def copy_static_assets(static_marker: bool = True) -> list[str]:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    copied = []
    for name in ("index.html", "styles.css", "app.js", "manifest.json"):
        source = STATIC_DIR / name
        target = DOCS_DIR / name
        text = source.read_text(encoding="utf-8")
        if name == "index.html":
            text = text.replace('href="/manifest.json"', 'href="manifest.json"')
            text = text.replace('href="/styles.css"', 'href="styles.css"')
            text = text.replace('src="/app.js"', 'src="app.js"')
            if static_marker and "window.OSLO_STATIC_SITE" not in text:
                text = text.replace(
                    '<script src="app.js"></script>',
                    '<script>window.OSLO_STATIC_SITE = true;</script>\n    <script src="app.js"></script>',
                )
        target.write_text(text, encoding="utf-8")
        copied.append(str(target.relative_to(ROOT)))
    return copied


def fundamentals_payload(server, symbols: list[str], refresh: bool) -> dict[str, Any]:
    rows = []
    errors = []
    for symbol in symbols:
        try:
            rows.append(server.cached_fundamental(symbol, refresh=refresh))
        except Exception as exc:  # source errors must remain visible in generated JSON
            errors.append({"symbol": symbol, "error": str(exc)})
    rows = server.apply_quarterly_statement_reviews(rows)
    return {
        "rows": rows,
        "errors": errors,
        "sourceNotes": server.source_notes(),
        "metricGuide": server.FUNDAMENTAL_METRIC_GUIDE,
        "dataValidation": server.fundamental_data_validation(rows),
    }


def watchlist_payload(server, name: str) -> dict[str, Any]:
    with server.connect() as con:
        lists = server.rows_to_dicts(con.execute("select * from watchlists order by name").fetchall())
        items = server.rows_to_dicts(
            con.execute(
                """
                select wi.watchlist_name, wi.symbol, wi.note, t.name, t.sector, t.industry
                from watchlist_items wi
                left join tickers t on t.symbol = wi.symbol
                where wi.watchlist_name = ?
                order by wi.symbol
                """,
                (name,),
            ).fetchall()
        )
    return {"watchlists": lists, "active": name, "items": items}


def consensus_payload(server) -> dict[str, Any]:
    with server.connect() as con:
        rows = server.rows_to_dicts(con.execute("select * from consensus_sources order by symbol, source").fetchall())
    for row in rows:
        row["staleStatus"] = server.stale_status(row.get("collected_at_epoch"))
        row["sourceType"] = server.consensus_source_type(row)
        row["reviewStatus"] = server.consensus_review_status(row)
        row["isReviewed"] = server.is_reviewed_consensus_row(row)
        row["isSourceLinked"] = server.is_source_linked_consensus_row(row)
    return {"sources": rows}


def build_static_outputs(server, inputs: dict[str, Any], output_dir: Path, refresh: bool, include_all_universe: bool) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    benchmark_dir = output_dir / "benchmarks"
    if benchmark_dir.exists():
        shutil.rmtree(benchmark_dir)
    benchmark_dir.mkdir(parents=True, exist_ok=True)

    watchlist_name = inputs["watchlist"]["watchlist"]
    watchlist_symbols = [item["symbol"] for item in inputs["watchlist"]["items"]]
    generated_at = utc_now()
    files: list[str] = []

    def emit(name: str, data: Any) -> None:
        write_json(output_dir / name, data)
        files.append(f"docs/data/{name}")

    emit("watchlist.json", watchlist_payload(server, watchlist_name))
    emit("screener-alerts.json", server.screener_alerts(name=watchlist_name, refresh=refresh))
    emit("technical-indicators-watchlist.json", server.technical_indicators(universe="watchlist", watchlist=watchlist_name, refresh=refresh))
    emit("technical-indicators-all.json", server.technical_indicators(universe="all", watchlist=watchlist_name, refresh=False))

    watchlist_overview = server.watchlist_overview(name=watchlist_name, refresh=refresh)
    emit("watchlist-overview.json", watchlist_overview)
    emit("fundamentals-watchlist.json", fundamentals_payload(server, watchlist_symbols, refresh=False))

    if include_all_universe:
        with server.connect() as con:
            all_symbols = [row["symbol"] for row in con.execute("select symbol from tickers order by symbol").fetchall()]
    else:
        all_symbols = watchlist_symbols
    fundamentals_all = fundamentals_payload(server, all_symbols, refresh=False)
    fundamentals_all["staticUniverseNote"] = (
        "First static beta maps the all-universe Fundamentals view to configured static symbols. "
        "Expand this intentionally when generation cost and yfinance rate limits are reviewed."
    )
    emit("fundamentals-all.json", fundamentals_all)

    event_payload = server.event_monitoring_payload(name=watchlist_name, refresh_newsweb=refresh)
    if event_payload.get("sourcePolicy"):
        event_payload["sourcePolicy"]["digestStatus"] = "scheduled/manual static generation"
        event_payload["sourcePolicy"]["limitation"] = (
            "Static Pages shows the last generated NewsWeb digest. It does not promise live on-demand news inside the browser."
        )
    emit("events.json", event_payload)
    emit("sources.json", server.source_notes())
    emit("consensus.json", consensus_payload(server))

    benchmark_files = {}
    for symbol in watchlist_symbols:
        payload = server.benchmark_for_symbol(symbol, refresh=False)
        filename = f"benchmarks/{urllib.parse.quote(symbol, safe='')}.json"
        emit(filename, payload)
        benchmark_files[symbol] = f"data/{filename}"

    manifest = {
        "generatedAt": generated_at,
        "betaRelease": "Beta v0.1.0",
        "mode": "static-github-pages",
        "refreshRequested": refresh,
        "watchlist": watchlist_name,
        "watchlistCount": len(watchlist_symbols),
        "inputFiles": [
            "data/watchlist.yml",
            "data/manual_consensus.yml",
            "data/peer_groups.yml",
            "data/sector_kpis.yml",
            "data/manual_events.yml",
            "data/quarterly_statement_reviews.yml",
        ],
        "outputFiles": files,
        "benchmarkFiles": benchmark_files,
        "sourceStatus": {
            "watchlistRows": len(watchlist_overview.get("rows", [])),
            "watchlistErrors": len(watchlist_overview.get("errors", [])),
            "screenerError": watchlist_overview.get("screenerError"),
            "technicalError": watchlist_overview.get("technicalError"),
            "eventErrors": event_payload.get("errors", []),
        },
        "watchlistEdit": {
            "sourceUrl": WATCHLIST_SOURCE_URL,
            "workflowUrl": WORKFLOW_URL,
            "codexPrompt": (
                "Please edit data/watchlist.yml in keresell-coder/oslo-market-workspace, keep the YAML schema valid, "
                "preserve the no-advice guardrails, and open a PR with the watchlist change. After merge, run the "
                "Static GitHub Pages data workflow or wait for the next scheduled refresh."
            ),
            "policy": "Public GitHub Pages JavaScript does not contain a GitHub write token. Watchlist edits happen through GitHub/Codex/PRs.",
        },
        "limitations": [
            "Static Pages shows the last generated dataset, not live data.",
            "Yahoo/yfinance, NewsWeb, and Oslo Screener sources are screening-grade and may be stale, delayed, incomplete, or wrong.",
            "Missing values stay missing. No buy/sell recommendation or standalone valuation label is produced.",
        ],
    }
    emit("manifest.json", manifest)
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build static GitHub Pages JSON data for Oslo Stock web-app.")
    parser.add_argument("--input-dir", type=Path, default=INPUT_DIR)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--refresh", action="store_true", help="Refresh upstream yfinance/NewsWeb/screener sources while generating.")
    parser.add_argument(
        "--cache-db",
        type=Path,
        default=ROOT / "app" / "data" / "oslo_workspace.sqlite3",
        help="Optional local SQLite cache to copy free-data cache tables from before generating.",
    )
    parser.add_argument(
        "--no-cache-db",
        action="store_true",
        help="Do not reuse local SQLite cache tables even when app/data/oslo_workspace.sqlite3 exists.",
    )
    parser.add_argument("--include-all-universe", action="store_true", help="Generate Fundamentals all-universe from all configured tickers.")
    parser.add_argument("--skip-assets", action="store_true", help="Do not copy app/static assets into docs/.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    inputs = load_inputs(args.input_dir)
    with tempfile.TemporaryDirectory(prefix="oslo-static-build-") as tmp:
        db_path = Path(tmp) / "static.sqlite3"
        server = import_app_server(db_path)
        server.init_db()
        if not args.no_cache_db:
            copy_cache_tables(args.cache_db, db_path)
        install_inputs(server, inputs)
        if not args.skip_assets:
            copy_static_assets(static_marker=True)
        manifest = build_static_outputs(
            server=server,
            inputs=inputs,
            output_dir=args.output_dir,
            refresh=args.refresh,
            include_all_universe=args.include_all_universe,
        )
    print(
        f"Generated {len(manifest['outputFiles'])} static data files for "
        f"{manifest['watchlistCount']} watchlist symbols at {manifest['generatedAt']}."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SchemaError as exc:
        print(f"Schema error: {exc}", file=sys.stderr)
        raise SystemExit(2)
