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


def cached_fundamental(symbol: str, refresh: bool = False) -> dict:
    symbol = normalize_symbol(symbol)
    now_epoch = int(time.time())
    with connect() as con:
        row = con.execute(
            "select payload, fetched_at_epoch from fundamentals_cache where symbol = ?",
            (symbol,),
        ).fetchone()
        if row and not refresh and now_epoch - int(row["fetched_at_epoch"]) < CACHE_TTL_SECONDS:
            payload = json.loads(row["payload"])
            payload.pop("valuationFlag", None)
            payload["cacheStatus"] = "cached"
            return payload

        payload = fetch_yfinance(symbol)
        payload.pop("valuationFlag", None)
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
            insert into tickers(symbol, name, sector, industry, source, created_at)
            values (?, ?, ?, ?, ?, ?)
            on conflict(symbol) do update set
                name = coalesce(excluded.name, tickers.name),
                sector = coalesce(excluded.sector, tickers.sector),
                industry = coalesce(excluded.industry, tickers.industry)
            """,
            (
                symbol,
                payload.get("name"),
                payload.get("sector"),
                payload.get("industry"),
                "Yahoo Finance via yfinance",
                utc_now(),
            ),
        )
        payload["cacheStatus"] = "fresh"
        return payload


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
        if parsed.path == "/api/fundamentals":
            return self.handle_fundamentals(parsed)
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
                join tickers t on t.symbol = wi.symbol
                where wi.watchlist_name = ?
                order by wi.symbol
                """,
                (name,),
            ).fetchall()
        send_json(self, {"watchlists": rows_to_dicts(lists), "active": name, "items": rows_to_dicts(items)})

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
            "limitations": "Delayed, rate-limited, not guaranteed complete. Verify important values against primary filings, company reports, or licensed data.",
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
    print(f"Oslo Market Workspace running at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down")


if __name__ == "__main__":
    main()
