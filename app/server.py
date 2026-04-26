from __future__ import annotations

import json
import re
import sqlite3
import sys
import time
import urllib.parse
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from statistics import median

try:
    import yfinance as yf
except Exception:  # pragma: no cover
    yf = None

try:
    import requests
    from bs4 import BeautifulSoup
except Exception:  # pragma: no cover
    requests = None
    BeautifulSoup = None


ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
DATA = ROOT / "data"
DB_PATH = DATA / "oslo_workspace.sqlite3"
CACHE_TTL_SECONDS = 60 * 60 * 6
CONSENSUS_FRESH_SECONDS = 60 * 60 * 24 * 3
CONSENSUS_OLD_SECONDS = 60 * 60 * 24 * 14
SCREENER_URL = "https://keresell-coder.github.io/oslo-screener-dashboard/"
SCREENER_CACHE_TTL_SECONDS = 60 * 15
SCREENER_CACHE: dict = {"fetched_at_epoch": 0, "payload": None}

INITIAL_WATCHLIST = [
    "NOD.OL",
    "LINK.OL",
    "VEND.OL",
    "DOFG.OL",
    "ODL.OL",
    "FRO.OL",
    "HAFNI.OL",
    "KOG.OL",
    "PUBLI.OL",
    "MOWI.OL",
]

PUBLISHED_SCREENER_TICKERS = [
    "AKSO.OL",
    "AUSS.OL",
    "BMA.OL",
    "EIOF.OL",
    "EPR.OL",
    "HELG.OL",
    "HEX.OL",
    "ININ.OL",
    "KOG.OL",
    "LSG.OL",
    "MOWI.OL",
    "NOD.OL",
    "PCIB.OL",
    "SOAG.OL",
    "SOGN.OL",
    "SUBC.OL",
    "TOM.OL",
    "VEI.OL",
    "ZAL.OL",
]

BENCHMARK_METRICS = [
    {
        "key": "trailingPE",
        "label": "TTM P/E",
        "unit": "x",
        "positionNote": "Lower/higher is context dependent; compare with growth, cyclicality, and margins.",
        "positiveOnly": True,
    },
    {
        "key": "forwardPE",
        "label": "Forward P/E",
        "unit": "x",
        "positionNote": "Forward data depends on estimates and source coverage.",
        "positiveOnly": True,
    },
    {
        "key": "priceToBook",
        "label": "P/B",
        "unit": "x",
        "positionNote": "Most useful for banks, asset-heavy sectors, and capital-intensive businesses.",
        "positiveOnly": True,
    },
    {
        "key": "enterpriseToEbitda",
        "label": "EV/EBITDA",
        "unit": "x",
        "positionNote": "Sector and leverage structure matter; not comparable across all business models.",
        "positiveOnly": True,
    },
    {
        "key": "dividendYield",
        "label": "Dividend yield",
        "unit": "%",
        "positionNote": "Higher yield can reflect payout strength or market risk.",
        "positiveOnly": False,
    },
    {
        "key": "targetUpsidePct",
        "label": "Target upside",
        "unit": "%",
        "positionNote": "Current MVP uses Yahoo/yfinance target fields only; verify against other consensus sources.",
        "positiveOnly": False,
    },
]

INITIAL_PEER_GROUPS = {
    "semiconductors-global": {
        "name": "Semiconductors - global",
        "description": "Initial manual peer group for Nordic Semiconductor. Review before relying on conclusions.",
        "source": "manual seed",
        "items": [
            ("NOD.OL", "focus", "Oslo"),
            ("STM", "peer", "International"),
            ("IFX.DE", "peer", "International"),
            ("NXPI", "peer", "International"),
            ("ON", "peer", "International"),
            ("SWKS", "peer", "International"),
        ],
    },
    "seafood-norway": {
        "name": "Seafood - Norway",
        "description": "Initial Oslo seafood peers for Mowi. Sector KPIs like EBIT/kg and biomass are not yet collected.",
        "source": "manual seed",
        "items": [
            ("MOWI.OL", "focus", "Oslo"),
            ("SALM.OL", "peer", "Oslo"),
            ("LSG.OL", "peer", "Oslo"),
            ("AUSS.OL", "peer", "Oslo"),
            ("GSF.OL", "peer", "Oslo"),
            ("BAKKA.OL", "peer", "Oslo"),
        ],
    },
    "tankers-global": {
        "name": "Tankers - global",
        "description": "Initial peer group for Frontline and Hafnia. NAV/fleet value is not yet collected.",
        "source": "manual seed",
        "items": [
            ("FRO.OL", "focus", "Oslo"),
            ("HAFNI.OL", "focus", "Oslo"),
            ("STNG", "peer", "International"),
            ("INSW", "peer", "International"),
            ("EURN.BR", "peer", "International"),
            ("TORM.CO", "peer", "International"),
        ],
    },
    "offshore-energy-services": {
        "name": "Offshore energy services",
        "description": "Initial peer group for offshore service/drilling exposure. Backlog, fleet, and day-rate data are not yet collected.",
        "source": "manual seed",
        "items": [
            ("DOFG.OL", "focus", "Oslo"),
            ("ODL.OL", "focus", "Oslo"),
            ("SUBC.OL", "peer", "Oslo"),
            ("AKSO.OL", "peer", "Oslo"),
            ("BORR.OL", "peer", "Oslo"),
            ("SDRL.OL", "peer", "Oslo"),
        ],
    },
    "defence-aerospace-europe": {
        "name": "Defence and aerospace - Europe",
        "description": "Initial European peer group for Kongsberg Gruppen. Segment mix differs materially by company.",
        "source": "manual seed",
        "items": [
            ("KOG.OL", "focus", "Oslo"),
            ("SAAB-B.ST", "peer", "International"),
            ("LDO.MI", "peer", "International"),
            ("HO.PA", "peer", "International"),
            ("BA.L", "peer", "International"),
        ],
    },
    "communications-software": {
        "name": "Communications software",
        "description": "Initial peer group for Link Mobility. Growth, gross margin, and leverage should be added before conclusions.",
        "source": "manual seed",
        "items": [
            ("LINK.OL", "focus", "Oslo"),
            ("SINCH.ST", "peer", "International"),
            ("CMCOM.AS", "peer", "International"),
        ],
    },
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_symbol(symbol: str) -> str:
    value = symbol.strip().upper()
    if value and "." not in value:
        value = f"{value}.OL"
    return value


def connect() -> sqlite3.Connection:
    DATA.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def init_db() -> None:
    with connect() as con:
        con.executescript(
            """
            create table if not exists tickers (
                symbol text primary key,
                name text,
                exchange text default 'Oslo Bors',
                sector text,
                industry text,
                source text default 'seed',
                created_at text not null
            );

            create table if not exists watchlists (
                name text primary key,
                created_at text not null
            );

            create table if not exists watchlist_items (
                watchlist_name text not null,
                symbol text not null,
                note text default '',
                created_at text not null,
                primary key (watchlist_name, symbol),
                foreign key (watchlist_name) references watchlists(name) on delete cascade,
                foreign key (symbol) references tickers(symbol) on delete cascade
            );

            create table if not exists fundamentals_cache (
                symbol text primary key,
                payload text not null,
                fetched_at_epoch integer not null,
                fetched_at text not null
            );

            create table if not exists fundamentals_snapshots (
                id integer primary key autoincrement,
                symbol text not null,
                payload text not null,
                fetched_at_epoch integer not null,
                fetched_at text not null
            );

            create table if not exists peer_groups (
                group_key text primary key,
                name text not null,
                description text default '',
                source text default 'manual',
                created_at text not null
            );

            create table if not exists peer_group_items (
                group_key text not null,
                symbol text not null,
                role text default 'peer',
                market text default '',
                source text default 'manual',
                created_at text not null,
                primary key (group_key, symbol),
                foreign key (group_key) references peer_groups(group_key) on delete cascade
            );

            create table if not exists consensus_sources (
                symbol text not null,
                source text not null,
                target_mean real,
                target_high real,
                target_low real,
                analyst_count real,
                recommendation text,
                recommendation_score real,
                source_url text,
                confidence text default 'single-source',
                method_note text default '',
                collected_at_epoch integer not null,
                collected_at text not null,
                primary key (symbol, source)
            );

            create table if not exists significant_events (
                id integer primary key autoincrement,
                symbol text not null,
                title text not null,
                category text default 'update',
                importance text default 'normal',
                source text default 'manual',
                url text default '',
                note text default '',
                published_at text,
                created_at_epoch integer not null,
                created_at text not null
            );
            """
        )
        now = utc_now()
        con.execute(
            "insert or ignore into watchlists(name, created_at) values (?, ?)",
            ("Core Watchlist", now),
        )
        for symbol in sorted(set(INITIAL_WATCHLIST + PUBLISHED_SCREENER_TICKERS)):
            con.execute(
                """
                insert or ignore into tickers(symbol, name, source, created_at)
                values (?, ?, ?, ?)
                """,
                (symbol, symbol.replace(".OL", ""), "seed/dashboard", now),
            )
        for symbol in INITIAL_WATCHLIST:
            con.execute(
                """
                insert or ignore into watchlist_items(watchlist_name, symbol, created_at)
                values (?, ?, ?)
                """,
                ("Core Watchlist", symbol, now),
            )
        seed_peer_groups(con, now)


def seed_peer_groups(con: sqlite3.Connection, now: str) -> None:
    for group_key, group in INITIAL_PEER_GROUPS.items():
        con.execute(
            """
            insert or ignore into peer_groups(group_key, name, description, source, created_at)
            values (?, ?, ?, ?, ?)
            """,
            (group_key, group["name"], group["description"], group["source"], now),
        )
        for symbol, role, market in group["items"]:
            normalized = normalize_symbol(symbol) if market == "Oslo" and "." not in symbol else symbol.upper()
            con.execute(
                """
                insert or ignore into tickers(symbol, name, source, created_at)
                values (?, ?, ?, ?)
                """,
                (normalized, normalized.replace(".OL", ""), "peer-group seed", now),
            )
            con.execute(
                """
                insert or ignore into peer_group_items(group_key, symbol, role, market, source, created_at)
                values (?, ?, ?, ?, ?, ?)
                """,
                (group_key, normalized, role, market, group["source"], now),
            )


def rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict]:
    return [dict(row) for row in rows]


def get_json_body(handler: SimpleHTTPRequestHandler) -> dict:
    length = int(handler.headers.get("content-length", "0"))
    if not length:
        return {}
    raw = handler.rfile.read(length)
    return json.loads(raw.decode("utf-8"))


def send_json(handler: SimpleHTTPRequestHandler, data: object, status: int = 200) -> None:
    payload = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("content-type", "application/json; charset=utf-8")
    handler.send_header("cache-control", "no-store")
    handler.send_header("content-length", str(len(payload)))
    handler.end_headers()
    handler.wfile.write(payload)


def fetch_yfinance(symbol: str) -> dict:
    if yf is None:
        raise RuntimeError("yfinance is not installed")

    ticker = yf.Ticker(symbol)
    info = ticker.get_info()
    now = utc_now()

    current_price = pick_number(info, "currentPrice", "regularMarketPrice", "previousClose")
    target = pick_number(info, "targetMeanPrice")
    upside = None
    if current_price and target:
        upside = (target / current_price - 1) * 100

    dividend_yield = pick_number(info, "dividendYield")
    if dividend_yield is not None and dividend_yield < 1:
        dividend_yield *= 100

    payload = {
        "symbol": symbol,
        "name": info.get("shortName") or info.get("longName") or symbol,
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "currency": info.get("currency") or "NOK",
        "price": current_price,
        "marketCap": pick_number(info, "marketCap"),
        "enterpriseValue": pick_number(info, "enterpriseValue"),
        "trailingPE": pick_number(info, "trailingPE"),
        "forwardPE": pick_number(info, "forwardPE"),
        "priceToBook": pick_number(info, "priceToBook"),
        "priceToSalesTrailing12Months": pick_number(info, "priceToSalesTrailing12Months"),
        "enterpriseToRevenue": pick_number(info, "enterpriseToRevenue"),
        "enterpriseToEbitda": pick_number(info, "enterpriseToEbitda"),
        "epsTrailingTwelveMonths": pick_number(info, "epsTrailingTwelveMonths", "trailingEps"),
        "epsForward": pick_number(info, "forwardEps"),
        "dividendYield": dividend_yield,
        "targetMeanPrice": target,
        "targetHighPrice": pick_number(info, "targetHighPrice"),
        "targetLowPrice": pick_number(info, "targetLowPrice"),
        "numberOfAnalystOpinions": pick_number(info, "numberOfAnalystOpinions"),
        "recommendationMean": pick_number(info, "recommendationMean"),
        "recommendationKey": info.get("recommendationKey"),
        "targetUpsidePct": upside,
        "targetPriceSource": "Yahoo Finance via yfinance",
        "targetPriceMethod": "Unknown from Yahoo/yfinance response. Treat as a third-party consensus field and verify against other sources.",
        "recommendationScale": "Yahoo/yfinance recommendation fields are not treated as a verified BUY/HOLD/SELL weighting in this app.",
        "pnAv": None,
        "evToEbit": None,
        "source": "Yahoo Finance via yfinance",
        "sourceReliability": "Open/free delayed data. Useful for screening; verify against filings or primary sources before acting.",
        "fetchedAt": now,
        "newswebUrl": f"https://newsweb.oslobors.no/search?query={urllib.parse.quote(symbol.replace('.OL', ''))}",
        "tradingViewSearchUrl": f"https://www.tradingview.com/search/?query={urllib.parse.quote(symbol.replace('.OL', ''))}",
    }
    return payload


def pick_number(info: dict, *keys: str) -> float | None:
    for key in keys:
        value = info.get(key)
        if isinstance(value, bool):
            continue
        if isinstance(value, (int, float)):
            return float(value)
    return None


def pick_body_number(body: dict, key: str) -> float | None:
    value = body.get(key)
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def stale_status(collected_at_epoch: int | None, fresh_seconds: int = CONSENSUS_FRESH_SECONDS) -> str:
    if not collected_at_epoch:
        return "missing"
    age = int(time.time()) - int(collected_at_epoch)
    if age <= fresh_seconds:
        return "fresh"
    if age <= CONSENSUS_OLD_SECONDS:
        return "stale"
    return "old"


def record_consensus_source(payload: dict) -> None:
    symbol = payload.get("symbol")
    if not symbol:
        return
    target_fields = [
        payload.get("targetMeanPrice"),
        payload.get("targetHighPrice"),
        payload.get("targetLowPrice"),
        payload.get("numberOfAnalystOpinions"),
        payload.get("recommendationKey"),
        payload.get("recommendationMean"),
    ]
    if all(value in (None, "") for value in target_fields):
        return
    now_epoch = int(time.time())
    collected_at = utc_now()
    with connect() as con:
        con.execute(
            """
            insert into consensus_sources(
                symbol, source, target_mean, target_high, target_low, analyst_count,
                recommendation, recommendation_score, source_url, confidence, method_note,
                collected_at_epoch, collected_at
            )
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            on conflict(symbol, source) do update set
                target_mean = excluded.target_mean,
                target_high = excluded.target_high,
                target_low = excluded.target_low,
                analyst_count = excluded.analyst_count,
                recommendation = excluded.recommendation,
                recommendation_score = excluded.recommendation_score,
                source_url = excluded.source_url,
                confidence = excluded.confidence,
                method_note = excluded.method_note,
                collected_at_epoch = excluded.collected_at_epoch,
                collected_at = excluded.collected_at
            """,
            (
                symbol,
                "Yahoo Finance via yfinance",
                payload.get("targetMeanPrice"),
                payload.get("targetHighPrice"),
                payload.get("targetLowPrice"),
                payload.get("numberOfAnalystOpinions"),
                payload.get("recommendationKey"),
                payload.get("recommendationMean"),
                f"https://finance.yahoo.com/quote/{urllib.parse.quote(symbol)}/analysis/",
                "single-source",
                "Yahoo/yfinance target and recommendation fields are not treated as verified consensus weighting.",
                now_epoch,
                collected_at,
            ),
        )


def consensus_for_symbol(symbol: str) -> dict:
    symbol = symbol.strip().upper()
    with connect() as con:
        rows = rows_to_dicts(
            con.execute(
                "select * from consensus_sources where symbol = ? order by source",
                (symbol,),
            ).fetchall()
        )
    for row in rows:
        row["staleStatus"] = stale_status(row.get("collected_at_epoch"))

    numeric_targets = [row["target_mean"] for row in rows if isinstance(row.get("target_mean"), (int, float))]
    analyst_counts = [row["analyst_count"] for row in rows if isinstance(row.get("analyst_count"), (int, float))]
    return {
        "symbol": symbol,
        "sources": rows,
        "sourceCount": len(rows),
        "targetMeanAcrossSources": median(numeric_targets) if numeric_targets else None,
        "analystCountKnown": sum(analyst_counts) if analyst_counts else None,
        "recommendationSummary": consensus_recommendation_summary(rows),
        "confidence": consensus_confidence(rows),
        "status": "missing" if not rows else ("multi-source" if len(rows) >= 2 else "single-source"),
        "note": "Consensus is not verified unless multiple source rows are present and reviewed.",
    }


def consensus_confidence(rows: list[dict]) -> str:
    if not rows:
        return "missing"
    fresh_rows = [row for row in rows if row.get("staleStatus") == "fresh"]
    reviewed_rows = [row for row in rows if row.get("confidence") in {"reviewed", "verified"}]
    if len(reviewed_rows) >= 2:
        return "higher"
    if len(fresh_rows) >= 2:
        return "medium"
    return "low"


def recommendation_bucket(value: str | None) -> str:
    text = (value or "").strip().lower()
    if not text:
        return "unknown"
    if any(token in text for token in ["strong buy", "buy", "outperform", "overweight", "accumulate"]):
        return "BUY"
    if any(token in text for token in ["sell", "underperform", "underweight", "reduce"]):
        return "SELL"
    if any(token in text for token in ["hold", "neutral", "market perform", "equal weight"]):
        return "HOLD"
    return text.upper()


def consensus_recommendation_summary(rows: list[dict]) -> dict:
    counts = {"BUY": 0, "HOLD": 0, "SELL": 0, "unknown": 0}
    for row in rows:
        bucket = recommendation_bucket(row.get("recommendation"))
        counts[bucket] = counts.get(bucket, 0) + 1
    known = {key: value for key, value in counts.items() if key != "unknown" and value}
    if not known:
        label = "n/a"
    else:
        label = sorted(known.items(), key=lambda item: (-item[1], item[0]))[0][0]
    return {
        "label": label,
        "counts": counts,
        "sourceCount": len(rows),
        "method": "Simple source-count summary. It is not analyst-count weighted unless source data explicitly supports that.",
    }


def significant_events_for_symbol(symbol: str, limit: int = 3) -> list[dict]:
    with connect() as con:
        rows = con.execute(
            """
            select *
            from significant_events
            where symbol = ?
            order by
              case importance when 'high' then 0 when 'medium' then 1 else 2 end,
              created_at_epoch desc
            limit ?
            """,
            (symbol, limit),
        ).fetchall()
    return rows_to_dicts(rows)


def event_alert_summary(events: list[dict]) -> dict:
    if not events:
        return {
            "level": "none",
            "label": "No tracked significant updates",
            "count": 0,
            "latest": None,
            "source": "manual/significant-events table",
        }
    high = [event for event in events if event.get("importance") == "high"]
    latest = events[0]
    return {
        "level": "high" if high else "normal",
        "label": latest.get("title") or "Significant update",
        "count": len(events),
        "latest": latest,
        "source": "manual/significant-events table",
    }


def enrich_fundamental_payload(payload: dict) -> dict:
    payload.setdefault("targetPriceSource", "Yahoo Finance via yfinance")
    payload.setdefault(
        "targetPriceMethod",
        "Unknown from Yahoo/yfinance response. Treat as a third-party consensus field and verify against other sources.",
    )
    payload.setdefault(
        "recommendationScale",
        "Yahoo/yfinance recommendation fields are not treated as a verified BUY/HOLD/SELL weighting in this app.",
    )
    record_consensus_source(payload)
    consensus = consensus_for_symbol(payload["symbol"])
    payload["consensus"] = consensus
    payload["targetSourceCount"] = consensus["sourceCount"]
    payload["targetConfidence"] = consensus["confidence"]
    payload["targetStatus"] = consensus["status"]
    return payload


def normalize_dashboard_ticker(ticker: str) -> str:
    value = re.sub(r"[^A-Z0-9.]", "", ticker.upper())
    if value and "." not in value:
        value = f"{value}.OL"
    return value


def fetch_screener_signals(refresh: bool = False) -> dict:
    now_epoch = int(time.time())
    cached = SCREENER_CACHE.get("payload")
    if cached and not refresh and now_epoch - int(SCREENER_CACHE["fetched_at_epoch"]) < SCREENER_CACHE_TTL_SECONDS:
        payload = dict(cached)
        payload["cacheStatus"] = "cached"
        return payload

    if requests is None or BeautifulSoup is None:
        raise RuntimeError("requests and beautifulsoup4 are required for screener signal extraction")

    response = requests.get(SCREENER_URL, timeout=20)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    signals = []
    for card in soup.select(".stock-card"):
        ticker_el = card.select_one(".stock-ticker")
        if not ticker_el:
            continue
        symbol = normalize_dashboard_ticker(ticker_el.get_text(" ", strip=True))
        badge_el = card.select_one(".signal-badge")
        section_el = None
        parent_section = card.find_parent("details")
        if parent_section:
            section_el = parent_section.select_one("summary")
        price_el = card.select_one(".stock-price")
        card_text = " ".join(card.get_text(" ", strip=True).split())
        signal = badge_el.get_text(" ", strip=True) if badge_el else ""
        section = section_el.get_text(" ", strip=True) if section_el else signal
        signals.append(
            {
                "symbol": symbol,
                "ticker": symbol.replace(".OL", ""),
                "signal": signal,
                "section": section,
                "price": price_el.get_text(" ", strip=True) if price_el else None,
                "summary": card_text[:260],
                "url": SCREENER_URL,
            }
        )

    payload = {
        "url": SCREENER_URL,
        "fetchedAt": utc_now(),
        "signals": signals,
        "count": len(signals),
        "sourceReliability": "Parsed from the published Oslo Screener Dashboard. This is a link/alert layer only; it does not verify the screener logic.",
    }
    SCREENER_CACHE["payload"] = payload
    SCREENER_CACHE["fetched_at_epoch"] = now_epoch
    result = dict(payload)
    result["cacheStatus"] = "fresh"
    return result


def watchlist_symbols(name: str = "Core Watchlist") -> list[str]:
    with connect() as con:
        return [
            row["symbol"]
            for row in con.execute(
                "select symbol from watchlist_items where watchlist_name = ? order by symbol",
                (name,),
            )
        ]


def screener_alerts(name: str = "Core Watchlist", refresh: bool = False) -> dict:
    screener = fetch_screener_signals(refresh=refresh)
    watched = set(watchlist_symbols(name))
    matches = [signal for signal in screener["signals"] if signal["symbol"] in watched]
    return {
        "watchlist": name,
        "matches": matches,
        "matchCount": len(matches),
        "watchlistCount": len(watched),
        "screenerCount": screener["count"],
        "fetchedAt": screener["fetchedAt"],
        "url": screener["url"],
        "cacheStatus": screener.get("cacheStatus"),
        "sourceReliability": screener["sourceReliability"],
    }


def safe_screener_alert_map(name: str = "Core Watchlist") -> tuple[dict, str | None]:
    try:
        alerts = screener_alerts(name=name, refresh=False)
        return {item["symbol"]: item for item in alerts.get("matches", [])}, None
    except Exception as exc:
        return {}, str(exc)


def watchlist_overview(name: str = "Core Watchlist") -> dict:
    with connect() as con:
        items = rows_to_dicts(
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

    screener_map, screener_error = safe_screener_alert_map(name)
    rows = []
    errors = []
    for item in items:
        symbol = item["symbol"]
        try:
            fundamental = cached_fundamental(symbol, refresh=False)
        except Exception as exc:
            fundamental = {}
            errors.append({"symbol": symbol, "error": str(exc)})

        consensus = consensus_for_symbol(symbol)
        events = significant_events_for_symbol(symbol)
        rows.append(
            {
                **item,
                "name": item.get("name") or fundamental.get("name") or symbol,
                "sector": item.get("sector") or fundamental.get("sector"),
                "industry": item.get("industry") or fundamental.get("industry"),
                "screenerSignal": screener_map.get(symbol),
                "consensusTarget": fundamental.get("targetMeanPrice"),
                "consensusTargetSource": fundamental.get("targetPriceSource"),
                "consensusTargetMethod": fundamental.get("targetPriceMethod"),
                "consensusTargetAcrossSources": consensus.get("targetMeanAcrossSources"),
                "targetUpsidePct": fundamental.get("targetUpsidePct"),
                "price": fundamental.get("price"),
                "consensusRecommendation": consensus.get("recommendationSummary", {}),
                "consensusConfidence": consensus.get("confidence"),
                "consensusStatus": consensus.get("status"),
                "consensusSourceCount": consensus.get("sourceCount"),
                "consensusAnalystCount": consensus.get("analystCountKnown"),
                "consensusSources": consensus.get("sources", []),
                "significantEvents": events,
                "eventAlert": event_alert_summary(events),
                "links": {
                    "yahoo": f"https://finance.yahoo.com/quote/{urllib.parse.quote(symbol)}",
                    "newsweb": f"https://newsweb.oslobors.no/search?query={urllib.parse.quote(symbol.replace('.OL', ''))}",
                    "screener": SCREENER_URL,
                },
            }
        )

    return {
        "watchlist": name,
        "rows": rows,
        "errors": errors,
        "screenerError": screener_error,
        "sourceNotes": {
            "consensus": "Target and recommendation fields are source-count summaries. They are not verified analyst-count weighted consensus unless reviewed sources are added.",
            "events": "Significant events are currently manual/tracked entries. Automated NewsWeb monitoring is still a later sprint.",
        },
    }


def cached_fundamental(symbol: str, refresh: bool = False, assume_oslo: bool = True) -> dict:
    symbol = normalize_symbol(symbol) if assume_oslo else symbol.strip().upper()
    now_epoch = int(time.time())
    with connect() as con:
        row = con.execute(
            "select payload, fetched_at_epoch from fundamentals_cache where symbol = ?",
            (symbol,),
        ).fetchone()
        if row and not refresh and now_epoch - int(row["fetched_at_epoch"]) < CACHE_TTL_SECONDS:
            payload = json.loads(row["payload"])
            payload.pop("valuationFlag", None)
            payload = enrich_fundamental_payload(payload)
            payload["cacheStatus"] = "cached"
            return payload

        payload = fetch_yfinance(symbol)
        payload.pop("valuationFlag", None)
        payload = enrich_fundamental_payload(payload)
        con.execute(
            """
            insert into fundamentals_cache(symbol, payload, fetched_at_epoch, fetched_at)
            values (?, ?, ?, ?)
            on conflict(symbol) do update set
                payload = excluded.payload,
                fetched_at_epoch = excluded.fetched_at_epoch,
                fetched_at = excluded.fetched_at
            """,
            (symbol, json.dumps(payload), now_epoch, payload["fetchedAt"]),
        )
        con.execute(
            """
            insert into fundamentals_snapshots(symbol, payload, fetched_at_epoch, fetched_at)
            values (?, ?, ?, ?)
            """,
            (symbol, json.dumps(payload), now_epoch, payload["fetchedAt"]),
        )
        con.execute(
            """
            insert into tickers(symbol, name, exchange, sector, industry, source, created_at)
            values (?, ?, ?, ?, ?, ?, ?)
            on conflict(symbol) do update set
                name = coalesce(excluded.name, tickers.name),
                exchange = coalesce(excluded.exchange, tickers.exchange),
                sector = coalesce(excluded.sector, tickers.sector),
                industry = coalesce(excluded.industry, tickers.industry)
            """,
            (
                symbol,
                payload.get("name"),
                "Oslo Bors" if symbol.endswith(".OL") else "International",
                payload.get("sector"),
                payload.get("industry"),
                "Yahoo Finance via yfinance",
                utc_now(),
            ),
        )
        payload["cacheStatus"] = "fresh"
        return payload


def numeric_metric(row: dict, key: str, positive_only: bool = False) -> float | None:
    value = row.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if positive_only and value <= 0:
        return None
    return float(value)


def pct_diff(current: float | None, benchmark: float | None) -> float | None:
    if current is None or benchmark in (None, 0):
        return None
    return (current / benchmark - 1) * 100


def percentile_position(current: float | None, values: list[float]) -> float | None:
    if current is None or not values:
        return None
    ordered = sorted(values)
    below_or_equal = sum(1 for value in ordered if value <= current)
    return below_or_equal / len(ordered) * 100


def peer_groups_for_symbol(symbol: str) -> list[dict]:
    symbol = symbol.strip().upper()
    with connect() as con:
        rows = con.execute(
            """
            select pg.group_key, pg.name, pg.description, pg.source
            from peer_groups pg
            join peer_group_items pgi on pgi.group_key = pg.group_key
            where pgi.symbol = ?
            order by pg.name
            """,
            (symbol,),
        ).fetchall()
    return rows_to_dicts(rows)


def peer_group_items(group_key: str) -> list[dict]:
    with connect() as con:
        rows = con.execute(
            """
            select pgi.group_key, pgi.symbol, pgi.role, pgi.market, pgi.source,
                   t.name, t.sector, t.industry
            from peer_group_items pgi
            left join tickers t on t.symbol = pgi.symbol
            where pgi.group_key = ?
            order by case when pgi.role = 'focus' then 0 else 1 end, pgi.symbol
            """,
            (group_key,),
        ).fetchall()
    return rows_to_dicts(rows)


def metric_summary(focus: dict, peers: list[dict], metric: dict) -> dict:
    key = metric["key"]
    focus_value = numeric_metric(focus, key, metric.get("positiveOnly", False))
    peer_values = [
        value
        for value in (numeric_metric(peer, key, metric.get("positiveOnly", False)) for peer in peers)
        if value is not None
    ]
    all_values = peer_values + ([focus_value] if focus_value is not None else [])
    peer_median = median(peer_values) if peer_values else None
    return {
        "key": key,
        "label": metric["label"],
        "unit": metric["unit"],
        "focusValue": focus_value,
        "peerCount": len(peer_values),
        "peerMedian": peer_median,
        "peerMin": min(peer_values) if peer_values else None,
        "peerMax": max(peer_values) if peer_values else None,
        "vsPeerMedianPct": pct_diff(focus_value, peer_median),
        "percentileInGroup": percentile_position(focus_value, all_values),
        "positionNote": metric["positionNote"],
    }


def own_history_summary(symbol: str) -> dict:
    with connect() as con:
        rows = con.execute(
            """
            select payload, fetched_at
            from fundamentals_snapshots
            where symbol = ?
            order by fetched_at_epoch asc
            """,
            (symbol,),
        ).fetchall()
        if not rows:
            cached = con.execute(
                "select payload, fetched_at from fundamentals_cache where symbol = ?",
                (symbol,),
            ).fetchall()
            rows = cached
    payloads = [json.loads(row["payload"]) for row in rows]
    summaries = []
    for metric in BENCHMARK_METRICS:
        values = [
            value
            for value in (
                numeric_metric(payload, metric["key"], metric.get("positiveOnly", False)) for payload in payloads
            )
            if value is not None
        ]
        current = values[-1] if values else None
        summaries.append(
            {
                "key": metric["key"],
                "label": metric["label"],
                "unit": metric["unit"],
                "observations": len(values),
                "current": current,
                "historyMedian": median(values) if values else None,
                "historyMin": min(values) if values else None,
                "historyMax": max(values) if values else None,
                "percentileInOwnHistory": percentile_position(current, values) if len(values) >= 2 else None,
            }
        )
    return {
        "symbol": symbol,
        "snapshotCount": len(rows),
        "firstSnapshotAt": rows[0]["fetched_at"] if rows else None,
        "lastSnapshotAt": rows[-1]["fetched_at"] if rows else None,
        "metrics": summaries,
        "status": "insufficient history" if len(rows) < 5 else "usable history",
        "requirement": "Own-history valuation context should use several observations across time; the MVP starts collecting snapshots now.",
    }


def sector_context(symbol: str) -> dict:
    with connect() as con:
        row = con.execute(
            "select symbol, name, exchange, sector, industry from tickers where symbol = ?",
            (symbol,),
        ).fetchone()
    payload = dict(row) if row else {"symbol": symbol}
    return {
        **payload,
        "status": "not configured",
        "message": "No Oslo sector-index or reviewed sector peer benchmark is configured yet.",
        "requirement": "Sector context should use a reviewed Oslo sector group, official sector index, or both before any valuation score is shown.",
    }


def benchmark_for_symbol(symbol: str, group_key: str | None = None, refresh: bool = False) -> dict:
    symbol = normalize_symbol(symbol)
    groups = peer_groups_for_symbol(symbol)
    if group_key:
        groups = [group for group in groups if group["group_key"] == group_key]
    if not groups:
        return {
            "symbol": symbol,
            "groups": [],
            "ownHistory": own_history_summary(symbol),
            "sectorContext": sector_context(symbol),
            "status": "no peer group",
            "message": "No peer group is configured for this symbol yet.",
        }

    results = []
    for group in groups:
        items = peer_group_items(group["group_key"])
        rows = []
        errors = []
        for item in items:
            try:
                row = cached_fundamental(item["symbol"], refresh=refresh, assume_oslo=False)
                row["peerRole"] = item["role"]
                row["peerMarket"] = item["market"]
                rows.append(row)
            except Exception as exc:
                errors.append({"symbol": item["symbol"], "error": str(exc)})

        focus = next((row for row in rows if row["symbol"] == symbol), None)
        if focus is None:
            try:
                focus = cached_fundamental(symbol, refresh=refresh, assume_oslo=False)
                focus["peerRole"] = "focus"
                focus["peerMarket"] = "Oslo"
                rows.append(focus)
            except Exception as exc:
                errors.append({"symbol": symbol, "error": str(exc)})
                focus = {"symbol": symbol}

        peers = [row for row in rows if row.get("symbol") != symbol]
        results.append(
            {
                **group,
                "items": rows,
                "errors": errors,
                "metricSummaries": [metric_summary(focus, peers, metric) for metric in BENCHMARK_METRICS],
                "coverage": {
                    "configuredPeers": len(items),
                    "loadedRows": len(rows),
                    "errors": len(errors),
                },
                "confidence": "review required",
                "confidenceReason": "Peer groups are manual seeds and yfinance coverage is incomplete; use as context, not a valuation call.",
            }
        )

    return {
        "symbol": symbol,
        "groups": results,
        "ownHistory": own_history_summary(symbol),
        "sectorContext": sector_context(symbol),
        "status": "benchmark context available",
        "policy": "No cheap/expensive label is produced. Metrics are descriptive until peer group, sector context, own-history coverage, and source quality are reviewed.",
    }


class AppHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC), **kwargs)

    def log_message(self, format: str, *args) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), format % args))

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/health":
            return send_json(self, {"ok": True, "time": utc_now()})
        if parsed.path == "/api/tickers":
            return self.handle_tickers()
        if parsed.path == "/api/watchlist":
            return self.handle_watchlist_get(parsed)
        if parsed.path == "/api/watchlist-overview":
            return self.handle_watchlist_overview(parsed)
        if parsed.path == "/api/fundamentals":
            return self.handle_fundamentals(parsed)
        if parsed.path == "/api/peer-groups":
            return self.handle_peer_groups(parsed)
        if parsed.path == "/api/benchmarks":
            return self.handle_benchmarks(parsed)
        if parsed.path == "/api/consensus":
            return self.handle_consensus_get(parsed)
        if parsed.path == "/api/events":
            return self.handle_events_get(parsed)
        if parsed.path == "/api/screener-signals":
            return self.handle_screener_signals(parsed)
        if parsed.path == "/api/screener-alerts":
            return self.handle_screener_alerts(parsed)
        if parsed.path == "/api/sources":
            return send_json(self, source_notes())
        return super().do_GET()

    def do_POST(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/tickers":
            return self.handle_ticker_post()
        if parsed.path == "/api/watchlist":
            return self.handle_watchlist_post()
        if parsed.path == "/api/consensus":
            return self.handle_consensus_post()
        if parsed.path == "/api/events":
            return self.handle_events_post()
        return send_json(self, {"error": "Not found"}, HTTPStatus.NOT_FOUND)

    def do_DELETE(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/watchlist":
            return self.handle_watchlist_delete(parsed)
        return send_json(self, {"error": "Not found"}, HTTPStatus.NOT_FOUND)

    def handle_tickers(self) -> None:
        with connect() as con:
            rows = con.execute("select * from tickers order by symbol").fetchall()
        send_json(self, {"tickers": rows_to_dicts(rows)})

    def handle_ticker_post(self) -> None:
        body = get_json_body(self)
        symbol = normalize_symbol(body.get("symbol", ""))
        if not symbol:
            return send_json(self, {"error": "symbol is required"}, HTTPStatus.BAD_REQUEST)
        with connect() as con:
            con.execute(
                """
                insert into tickers(symbol, name, source, created_at)
                values (?, ?, ?, ?)
                on conflict(symbol) do update set name = coalesce(excluded.name, tickers.name)
                """,
                (symbol, body.get("name") or symbol.replace(".OL", ""), "manual", utc_now()),
            )
        send_json(self, {"ok": True, "symbol": symbol})

    def handle_watchlist_get(self, parsed) -> None:
        qs = urllib.parse.parse_qs(parsed.query)
        name = qs.get("name", ["Core Watchlist"])[0]
        with connect() as con:
            lists = con.execute("select * from watchlists order by name").fetchall()
            items = con.execute(
                """
                select wi.watchlist_name, wi.symbol, wi.note, t.name, t.sector, t.industry
                from watchlist_items wi
                left join tickers t on t.symbol = wi.symbol
                where wi.watchlist_name = ?
                order by wi.symbol
                """,
                (name,),
            ).fetchall()
        send_json(self, {"watchlists": rows_to_dicts(lists), "active": name, "items": rows_to_dicts(items)})

    def handle_watchlist_overview(self, parsed) -> None:
        qs = urllib.parse.parse_qs(parsed.query)
        name = qs.get("name", ["Core Watchlist"])[0]
        send_json(self, watchlist_overview(name))

    def handle_watchlist_post(self) -> None:
        body = get_json_body(self)
        name = body.get("watchlist") or "Core Watchlist"
        symbol = normalize_symbol(body.get("symbol", ""))
        if not symbol:
            return send_json(self, {"error": "symbol is required"}, HTTPStatus.BAD_REQUEST)
        now = utc_now()
        with connect() as con:
            con.execute("insert or ignore into watchlists(name, created_at) values (?, ?)", (name, now))
            con.execute(
                "insert or ignore into tickers(symbol, name, source, created_at) values (?, ?, ?, ?)",
                (symbol, symbol.replace(".OL", ""), "manual/watchlist", now),
            )
            con.execute(
                """
                insert into watchlist_items(watchlist_name, symbol, note, created_at)
                values (?, ?, ?, ?)
                on conflict(watchlist_name, symbol) do update set note = excluded.note
                """,
                (name, symbol, body.get("note", ""), now),
            )
        send_json(self, {"ok": True, "symbol": symbol, "watchlist": name})

    def handle_watchlist_delete(self, parsed) -> None:
        qs = urllib.parse.parse_qs(parsed.query)
        name = qs.get("watchlist", ["Core Watchlist"])[0]
        symbol = normalize_symbol(qs.get("symbol", [""])[0])
        if not symbol:
            return send_json(self, {"error": "symbol is required"}, HTTPStatus.BAD_REQUEST)
        with connect() as con:
            con.execute(
                "delete from watchlist_items where watchlist_name = ? and symbol = ?",
                (name, symbol),
            )
        send_json(self, {"ok": True})

    def handle_fundamentals(self, parsed) -> None:
        qs = urllib.parse.parse_qs(parsed.query)
        refresh = qs.get("refresh", ["0"])[0] == "1"
        universe = qs.get("universe", ["watchlist"])[0]
        symbols = qs.get("symbols", [])
        if symbols:
            selected = [normalize_symbol(s) for raw in symbols for s in raw.split(",") if s.strip()]
        elif universe == "all":
            with connect() as con:
                selected = [row["symbol"] for row in con.execute("select symbol from tickers order by symbol")]
        else:
            with connect() as con:
                selected = [
                    row["symbol"]
                    for row in con.execute(
                        "select symbol from watchlist_items where watchlist_name = ? order by symbol",
                        ("Core Watchlist",),
                    )
                ]

        rows = []
        errors = []
        for symbol in selected:
            try:
                rows.append(cached_fundamental(symbol, refresh=refresh))
            except Exception as exc:
                errors.append({"symbol": symbol, "error": str(exc)})
        send_json(self, {"rows": rows, "errors": errors, "sourceNotes": source_notes()})

    def handle_peer_groups(self, parsed) -> None:
        qs = urllib.parse.parse_qs(parsed.query)
        symbol = qs.get("symbol", [""])[0].strip()
        with connect() as con:
            if symbol:
                groups = peer_groups_for_symbol(normalize_symbol(symbol))
            else:
                groups = rows_to_dicts(con.execute("select * from peer_groups order by name").fetchall())
        send_json(self, {"groups": groups})

    def handle_benchmarks(self, parsed) -> None:
        qs = urllib.parse.parse_qs(parsed.query)
        symbol = qs.get("symbol", [""])[0].strip()
        if not symbol:
            return send_json(self, {"error": "symbol is required"}, HTTPStatus.BAD_REQUEST)
        group_key = qs.get("group", [None])[0]
        refresh = qs.get("refresh", ["0"])[0] == "1"
        send_json(self, benchmark_for_symbol(symbol, group_key=group_key, refresh=refresh))

    def handle_consensus_get(self, parsed) -> None:
        qs = urllib.parse.parse_qs(parsed.query)
        symbol = qs.get("symbol", [""])[0].strip()
        if symbol:
            return send_json(self, consensus_for_symbol(normalize_symbol(symbol)))
        with connect() as con:
            rows = rows_to_dicts(con.execute("select * from consensus_sources order by symbol, source").fetchall())
        for row in rows:
            row["staleStatus"] = stale_status(row.get("collected_at_epoch"))
        send_json(self, {"sources": rows})

    def handle_consensus_post(self) -> None:
        body = get_json_body(self)
        symbol = normalize_symbol(body.get("symbol", ""))
        source = body.get("source", "").strip()
        if not symbol or not source:
            return send_json(self, {"error": "symbol and source are required"}, HTTPStatus.BAD_REQUEST)
        now_epoch = int(time.time())
        collected_at = utc_now()
        with connect() as con:
            con.execute(
                """
                insert into consensus_sources(
                    symbol, source, target_mean, target_high, target_low, analyst_count,
                    recommendation, recommendation_score, source_url, confidence, method_note,
                    collected_at_epoch, collected_at
                )
                values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                on conflict(symbol, source) do update set
                    target_mean = excluded.target_mean,
                    target_high = excluded.target_high,
                    target_low = excluded.target_low,
                    analyst_count = excluded.analyst_count,
                    recommendation = excluded.recommendation,
                    recommendation_score = excluded.recommendation_score,
                    source_url = excluded.source_url,
                    confidence = excluded.confidence,
                    method_note = excluded.method_note,
                    collected_at_epoch = excluded.collected_at_epoch,
                    collected_at = excluded.collected_at
                """,
                (
                    symbol,
                    source,
                    pick_body_number(body, "targetMean"),
                    pick_body_number(body, "targetHigh"),
                    pick_body_number(body, "targetLow"),
                    pick_body_number(body, "analystCount"),
                    body.get("recommendation"),
                    pick_body_number(body, "recommendationScore"),
                    body.get("sourceUrl"),
                    body.get("confidence", "manual"),
                    body.get("methodNote", "Manual consensus/source entry."),
                    now_epoch,
                    collected_at,
                ),
            )
        send_json(self, consensus_for_symbol(symbol))

    def handle_events_get(self, parsed) -> None:
        qs = urllib.parse.parse_qs(parsed.query)
        symbol = qs.get("symbol", [""])[0].strip()
        with connect() as con:
            if symbol:
                rows = rows_to_dicts(
                    con.execute(
                        "select * from significant_events where symbol = ? order by created_at_epoch desc",
                        (normalize_symbol(symbol),),
                    ).fetchall()
                )
            else:
                rows = rows_to_dicts(
                    con.execute("select * from significant_events order by created_at_epoch desc").fetchall()
                )
        send_json(self, {"events": rows})

    def handle_events_post(self) -> None:
        body = get_json_body(self)
        symbol = normalize_symbol(body.get("symbol", ""))
        title = body.get("title", "").strip()
        if not symbol or not title:
            return send_json(self, {"error": "symbol and title are required"}, HTTPStatus.BAD_REQUEST)
        now_epoch = int(time.time())
        created_at = utc_now()
        with connect() as con:
            con.execute(
                """
                insert into significant_events(
                    symbol, title, category, importance, source, url, note,
                    published_at, created_at_epoch, created_at
                )
                values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    symbol,
                    title,
                    body.get("category", "update"),
                    body.get("importance", "normal"),
                    body.get("source", "manual"),
                    body.get("url", ""),
                    body.get("note", ""),
                    body.get("publishedAt"),
                    now_epoch,
                    created_at,
                ),
            )
        send_json(self, {"events": significant_events_for_symbol(symbol, limit=10)})

    def handle_screener_signals(self, parsed) -> None:
        qs = urllib.parse.parse_qs(parsed.query)
        refresh = qs.get("refresh", ["0"])[0] == "1"
        try:
            send_json(self, fetch_screener_signals(refresh=refresh))
        except Exception as exc:
            send_json(self, {"error": str(exc)}, HTTPStatus.BAD_GATEWAY)

    def handle_screener_alerts(self, parsed) -> None:
        qs = urllib.parse.parse_qs(parsed.query)
        refresh = qs.get("refresh", ["0"])[0] == "1"
        name = qs.get("watchlist", ["Core Watchlist"])[0]
        try:
            send_json(self, screener_alerts(name=name, refresh=refresh))
        except Exception as exc:
            send_json(self, {"error": str(exc)}, HTTPStatus.BAD_GATEWAY)


def source_notes() -> dict:
    return {
        "existingDashboard": {
            "url": "https://keresell-coder.github.io/oslo-screener-dashboard/",
            "verification": "Fetched successfully from GitHub Pages during setup. The page is treated as an embedded external artifact and is not edited by this MVP. Watchlist alerts parse ticker/signal cards from the published page.",
        },
        "yfinance": {
            "use": "Open/free Yahoo Finance data for price, multiples, analyst target fields where available.",
            "limitations": "Delayed, rate-limited, not guaranteed complete. Target-price and recommendation fields are labeled as Yahoo/yfinance only and should be verified against other consensus sources.",
        },
        "benchmarks": {
            "use": "Manual peer groups plus cached yfinance metrics for descriptive relative context.",
            "limitations": "No cheap/expensive verdict is produced. Peer groups are initial seeds and require review; own-history context starts accumulating from local refresh snapshots.",
        },
        "newsweb": {
            "use": "Ticker-specific search links in the MVP.",
            "limitations": "The public site is JavaScript-driven and no stable public API/RSS feed was confirmed during setup.",
        },
        "tradingView": {
            "use": "Search links only in this MVP.",
            "limitations": "Consensus and target-price fields are not pulled automatically because there is no confirmed open public API for this use.",
        },
    }


def main() -> None:
    init_db()
    host = "127.0.0.1"
    port = 8765
    server = ThreadingHTTPServer((host, port), AppHandler)
    print(f"Oslo Stock web-app running at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down")


if __name__ == "__main__":
    main()
