from __future__ import annotations

import json
import math
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
PRICE_HISTORY_MIN_OBSERVATIONS = 120
SNAPSHOT_HISTORY_MIN_OBSERVATIONS = 5

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

OWN_HISTORY_METRIC_KEYS = {"trailingPE", "forwardPE", "priceToBook", "enterpriseToEbitda", "dividendYield"}

PEER_GROUP_STATUSES = {"draft", "reviewed", "trusted"}
PEER_ROLE_LABELS = {
    "focus company",
    "Oslo peer",
    "Nordic peer",
    "European peer",
    "international peer",
    "sector index/proxy",
}
NORDIC_SUFFIXES = (".OL", ".ST", ".CO", ".HE", ".IC")
EUROPEAN_SUFFIXES = (".AS", ".BR", ".DE", ".L", ".MI", ".PA", ".SW")

INITIAL_PEER_GROUPS = {
    "semiconductors-global": {
        "name": "Low-power wireless semiconductors - Nordic Semiconductor",
        "description": "Reviewed peer set for Nordic Semiconductor. Focus is low-power wireless connectivity, IoT SoCs/modules, embedded processing, and adjacent mixed-signal semiconductors.",
        "status": "reviewed",
        "curator_note": "Nordic has no close Oslo-listed semiconductor peer. European and international peers are included by product overlap, but several are much broader and larger semiconductor groups.",
        "source": "manual research 2026-04-27",
        "items": [
            {"symbol": "NOD.OL", "role": "focus company", "market": "Oslo", "note": "Focus company: fabless low-power wireless connectivity chips and platforms for IoT."},
            {"symbol": "UBXN.SW", "role": "European peer", "market": "Switzerland", "note": "Wireless, positioning, and IoT modules. Closer end-market overlap than broad semiconductor names, but module/system mix differs."},
            {"symbol": "SLAB", "role": "international peer", "market": "US", "note": "Wireless MCUs and IoT connectivity are close product comparables; US listing and broader embedded portfolio."},
            {"symbol": "STM", "role": "European peer", "market": "Europe/US", "note": "Large European semiconductor group with microcontrollers, wireless, sensors, and automotive/industrial exposure; broader than Nordic."},
            {"symbol": "IFX.DE", "role": "European peer", "market": "Germany", "note": "European semiconductor peer with IoT, power, automotive, and security exposure; much broader product mix."},
            {"symbol": "NXPI", "role": "European peer", "market": "Netherlands/US", "note": "Embedded processing, connectivity, and automotive/industrial exposure; scale and segment mix differ."},
            {"symbol": "ON", "role": "international peer", "market": "US", "note": "Mixed-signal/power semiconductor peer with industrial and automotive exposure; less direct wireless overlap."},
        ],
    },
    "seafood-norway": {
        "name": "Atlantic salmon farming - Mowi",
        "description": "Reviewed peer set for Mowi. Focus is listed Atlantic salmon farming and vertically integrated seafood exposure, prioritising Oslo and Nordic listings.",
        "status": "reviewed",
        "curator_note": "Best context still needs sector KPIs such as harvest volume, EBIT/kg, licence geography, biological costs, feed exposure, and contract/share of spot sales.",
        "source": "manual research 2026-04-27",
        "items": [
            {"symbol": "MOWI.OL", "role": "focus company", "market": "Oslo", "note": "Focus company: global integrated Atlantic salmon producer with feed, farming, processing, and sales."},
            {"symbol": "SALM.OL", "role": "Oslo peer", "market": "Oslo", "note": "Large Norwegian salmon farmer; close listed salmon farming peer."},
            {"symbol": "LSG.OL", "role": "Oslo peer", "market": "Oslo", "note": "Norwegian seafood group with salmon farming and whitefish/wild-catch exposure; useful but not pure salmon."},
            {"symbol": "GSF.OL", "role": "Oslo peer", "market": "Oslo", "note": "Norwegian salmon farmer with regional biological and cost differences versus Mowi."},
            {"symbol": "BAKKA.OL", "role": "Nordic peer", "market": "Faroe/Oslo", "note": "Faroese and Scottish integrated salmon farmer; strong Nordic salmon peer, listed in Oslo."},
            {"symbol": "AUSS.OL", "role": "Oslo peer", "market": "Oslo", "note": "Seafood holding company with Leroy ownership and pelagic exposure; useful sector proxy but indirect."},
            {"symbol": "MAS.OL", "role": "Oslo peer", "market": "Oslo", "note": "Smaller Norwegian salmon farmer; useful for Oslo salmon context but scale differs materially."},
            {"symbol": "SALME.OL", "role": "Oslo peer", "market": "Oslo", "note": "Land-based salmon exposure. Include as adjacent context only; business model and risk profile differ."},
        ],
    },
    "tankers-global": {
        "name": "Crude tankers - Frontline",
        "description": "Reviewed peer set for Frontline. Focus is listed crude tanker owners/operators with VLCC, Suezmax, and adjacent Aframax/LR2 exposure.",
        "status": "reviewed",
        "curator_note": "NAV, fleet age, vessel class mix, charter coverage, scrubber exposure, and spot-rate exposure matter more than generic multiples for tanker context.",
        "source": "manual research 2026-04-27",
        "items": [
            {"symbol": "FRO.OL", "role": "focus company", "market": "Oslo", "note": "Focus company: crude tanker owner/operator with VLCC, Suezmax, and LR2/Aframax exposure."},
            {"symbol": "OET.OL", "role": "Oslo peer", "market": "Oslo", "note": "Modern VLCC/Suezmax crude tanker peer listed in Oslo and New York."},
            {"symbol": "DHT", "role": "international peer", "market": "US", "note": "VLCC-focused crude tanker peer; useful for large crude tanker exposure."},
            {"symbol": "TNK", "role": "international peer", "market": "US", "note": "Mid-size crude tanker peer with Suezmax/Aframax exposure."},
            {"symbol": "INSW", "role": "international peer", "market": "US", "note": "Mixed crude and product tanker peer; useful but segment mix overlaps with both Frontline and Hafnia."},
            {"symbol": "NAT", "role": "international peer", "market": "US", "note": "Suezmax-focused crude tanker peer; narrower class exposure than Frontline."},
        ],
    },
    "product-tankers-hafnia": {
        "name": "Product tankers - Hafnia",
        "description": "Reviewed peer set for Hafnia. Focus is listed product and chemical tanker owners/operators.",
        "status": "reviewed",
        "curator_note": "Product tanker comparisons should use fleet class mix, clean/dirty product exposure, chemical capability, spot/pool exposure, and fleet age before drawing conclusions.",
        "source": "manual research 2026-04-27",
        "items": [
            {"symbol": "HAFNI.OL", "role": "focus company", "market": "Oslo", "note": "Focus company: product and chemical tanker owner/operator with LR2, LR1, MR, Handy, and chemical exposure."},
            {"symbol": "TORM.CO", "role": "Nordic peer", "market": "Denmark", "note": "Danish product tanker owner/operator; closest Nordic listed product tanker peer."},
            {"symbol": "STNG", "role": "international peer", "market": "US", "note": "Large listed product tanker peer with LR/MR exposure."},
            {"symbol": "ASC", "role": "international peer", "market": "US", "note": "Product and chemical tanker peer; smaller scale than Hafnia."},
            {"symbol": "DIS.MI", "role": "European peer", "market": "Italy", "note": "European product tanker peer through d'Amico International Shipping; useful regional listed comparator."},
            {"symbol": "INSW", "role": "international peer", "market": "US", "note": "Mixed crude/product tanker peer; include for cross-segment listed tanker context."},
        ],
    },
    "offshore-energy-services": {
        "name": "Subsea and offshore services - DOF",
        "description": "Reviewed peer set for DOF Group. Focus is subsea services, offshore support vessels, IMR/light construction, and adjacent offshore engineering/services.",
        "status": "reviewed",
        "curator_note": "DOF should not be benchmarked directly against drilling-rig owners. Backlog, vessel mix, utilisation, day rates, leverage, and project risk are required for useful sector context.",
        "source": "manual research 2026-04-27",
        "items": [
            {"symbol": "DOFG.OL", "role": "focus company", "market": "Oslo", "note": "Focus company: integrated subsea services, offshore operations, marine services, OSVs, and subsea assets."},
            {"symbol": "SUBC.OL", "role": "Oslo peer", "market": "Oslo", "note": "Subsea engineering, construction, and offshore project services. Larger and more EPCI/project-oriented than DOF."},
            {"symbol": "SOFF.OL", "role": "Oslo peer", "market": "Oslo", "note": "Offshore support vessel owner/operator; close OSV fleet context but different service integration."},
            {"symbol": "AKSO.OL", "role": "Oslo peer", "market": "Oslo", "note": "Offshore engineering/products/services peer. Useful adjacent context, not a direct vessel/subsea fleet peer."},
            {"symbol": "TDW", "role": "international peer", "market": "US", "note": "Large OSV peer; useful international offshore vessel context."},
            {"symbol": "FTI", "role": "international peer", "market": "US/Europe", "note": "TechnipFMC provides subsea systems and services; adjacent global subsea peer with different equipment/EPCI mix."},
            {"symbol": "OII", "role": "international peer", "market": "US", "note": "ROV, subsea services, and offshore engineered services; useful subsea services comparator."},
            {"symbol": "HLX", "role": "international peer", "market": "US", "note": "Offshore energy services and well intervention; adjacent subsea/offshore service exposure."},
        ],
    },
    "offshore-drilling-rigs": {
        "name": "Offshore drilling rigs - Odfjell Drilling",
        "description": "Reviewed peer set for Odfjell Drilling. Focus is offshore drilling contractors, with notes separating harsh-environment floaters from jack-up and broader deepwater peers.",
        "status": "reviewed",
        "curator_note": "Rig type, harsh-environment capability, contract backlog, day rates, utilisation, leverage, and fleet ownership/management model are critical. Jack-up peers are included as Oslo context but are not direct harsh-environment floater peers.",
        "source": "manual research 2026-04-27",
        "items": [
            {"symbol": "ODL.OL", "role": "focus company", "market": "Oslo", "note": "Focus company: harsh-environment semi-submersible drilling units and drilling services."},
            {"symbol": "NOL.OL", "role": "Oslo peer", "market": "Oslo", "note": "Harsh-environment semi-submersible exposure; closer rig-type context where data is available."},
            {"symbol": "SDRL.OL", "role": "Oslo peer", "market": "Oslo", "note": "Deepwater drilling contractor with floater exposure; broader global fleet."},
            {"symbol": "BORR.OL", "role": "Oslo peer", "market": "Oslo", "note": "Jack-up drilling contractor. Useful Oslo drilling context but shallow-water jack-ups differ from Odfjell's harsh-environment floaters."},
            {"symbol": "SHLF.OL", "role": "Oslo peer", "market": "Oslo", "note": "Jack-up drilling contractor. Include for Oslo-listed drilling context, not direct floater comparability."},
            {"symbol": "RIG", "role": "international peer", "market": "US", "note": "Large offshore drilling contractor with ultra-deepwater and harsh-environment exposure."},
            {"symbol": "VAL", "role": "international peer", "market": "US", "note": "Global offshore driller with floaters and jack-ups; broader fleet than Odfjell."},
            {"symbol": "NE", "role": "international peer", "market": "US", "note": "Global offshore drilling contractor; useful international rig-cycle peer."},
        ],
    },
    "defence-aerospace-europe": {
        "name": "Defence, aerospace and maritime technology - Kongsberg",
        "description": "Reviewed peer set for Kongsberg Gruppen. Focus is European defence/aerospace primes, defence electronics, sensors, missiles, maritime technology, and relevant Nordic defence specialists.",
        "status": "reviewed",
        "curator_note": "Kongsberg is a mixed defence, aerospace, discovery, and maritime technology group. The proposed maritime demerger means historical comparisons should be treated carefully.",
        "source": "manual research 2026-04-27",
        "items": [
            {"symbol": "KOG.OL", "role": "focus company", "market": "Oslo", "note": "Focus company: defence, aerospace, discovery, space, sensors, missiles, and maritime technology exposure."},
            {"symbol": "KIT.OL", "role": "Oslo peer", "market": "Oslo", "note": "Electronics manufacturing/services supplier with defence/aerospace exposure. Oslo industrial proxy, not a defence prime."},
            {"symbol": "SAAB-B.ST", "role": "Nordic peer", "market": "Sweden", "note": "Closest Nordic defence/aerospace prime by business profile."},
            {"symbol": "MILDEF.ST", "role": "Nordic peer", "market": "Sweden", "note": "Defence IT and rugged hardware specialist; smaller and narrower than Kongsberg."},
            {"symbol": "IVSO.ST", "role": "Nordic peer", "market": "Sweden", "note": "Tactical communication/hearing protection specialist; niche defence electronics peer."},
            {"symbol": "RHM.DE", "role": "European peer", "market": "Germany", "note": "European defence systems peer, especially land systems and ammunition; product mix differs."},
            {"symbol": "HAG.DE", "role": "European peer", "market": "Germany", "note": "Defence sensor/electronics specialist; useful for Kongsberg's sensor and surveillance exposure."},
            {"symbol": "HO.PA", "role": "European peer", "market": "France", "note": "Defence, aerospace, cyber, digital identity, and secure communications peer; broader than Kongsberg."},
            {"symbol": "LDO.MI", "role": "European peer", "market": "Italy", "note": "Aerospace, defence, helicopters, electronics, cyber, and space peer; broader segment mix."},
            {"symbol": "BA.L", "role": "European peer", "market": "UK", "note": "Large defence/aerospace prime; useful global defence benchmark but much larger scale."},
            {"symbol": "AIR.PA", "role": "European peer", "market": "Europe", "note": "Airbus Defence and Space exposure is relevant, but Airbus is dominated by commercial aerospace."},
        ],
    },
    "communications-software": {
        "name": "CPaaS and customer messaging - LINK Mobility",
        "description": "Reviewed peer set for LINK Mobility. Focus is listed CPaaS, mobile messaging, and adjacent customer engagement software.",
        "status": "reviewed",
        "curator_note": "LINK has no close Oslo-listed peer. Gross margin, organic growth, message volumes, regional mix, customer concentration, leverage, and operator pass-through costs are needed for useful context.",
        "source": "manual research 2026-04-27",
        "items": [
            {"symbol": "LINK.OL", "role": "focus company", "market": "Oslo", "note": "Focus company: CPaaS, mobile messaging, and digital customer engagement, with strong European SMS footprint."},
            {"symbol": "SINCH.ST", "role": "Nordic peer", "market": "Sweden", "note": "Closest listed Nordic CPaaS/cloud communications peer; larger and broader than LINK."},
            {"symbol": "CMCOM.AS", "role": "European peer", "market": "Netherlands", "note": "European CPaaS and conversational commerce/customer engagement peer."},
            {"symbol": "TWLO", "role": "international peer", "market": "US", "note": "Global cloud communications/API platform peer; much larger and more software/API-heavy."},
            {"symbol": "BRZE", "role": "international peer", "market": "US", "note": "Customer engagement platform with messaging channels; adjacent software peer, not telecom aggregator."},
            {"symbol": "KVYO", "role": "international peer", "market": "US", "note": "Marketing automation and messaging/email platform; adjacent customer engagement peer."},
            {"symbol": "ROUTE.NS", "role": "international peer", "market": "India", "note": "CPaaS/mobile messaging peer with emerging-market exposure; listing and ownership context differ."},
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


def normalize_peer_role(role: str, market: str = "") -> str:
    value = (role or "").strip()
    if value in PEER_ROLE_LABELS:
        return value
    legacy = value.lower()
    market_value = (market or "").strip().lower()
    if legacy == "focus":
        return "focus company"
    if legacy == "peer" and market_value == "oslo":
        return "Oslo peer"
    if legacy == "peer" and market_value in {"international", "global"}:
        return "international peer"
    if legacy == "peer" and market_value == "nordic":
        return "Nordic peer"
    if legacy == "peer" and market_value in {"europe", "european"}:
        return "European peer"
    if legacy in {"index", "proxy", "sector"}:
        return "sector index/proxy"
    return "international peer" if value else "Oslo peer"


def normalize_peer_status(status: str) -> str:
    value = (status or "draft").strip().lower()
    return value if value in PEER_GROUP_STATUSES else "draft"


def normalize_group_key(value: str) -> str:
    key = re.sub(r"[^a-z0-9]+", "-", (value or "").strip().lower()).strip("-")
    return key[:80] or f"peer-group-{int(time.time())}"


def normalize_peer_symbol(symbol: str, role: str, market: str) -> str:
    value = symbol.strip().upper()
    role_value = normalize_peer_role(role, market)
    market_value = (market or "").strip().lower()
    if value and "." not in value and (role_value in {"focus company", "Oslo peer"} or market_value == "oslo"):
        return normalize_symbol(value)
    return value


def peer_role_for_symbol(symbol: str, focus_symbol: str | None = None) -> str:
    value = symbol.strip().upper()
    if focus_symbol and value == focus_symbol.strip().upper():
        return "focus company"
    if value.endswith(".OL"):
        return "Oslo peer"
    if value.endswith(NORDIC_SUFFIXES):
        return "Nordic peer"
    if value.endswith(EUROPEAN_SUFFIXES):
        return "European peer"
    return "international peer"


def peer_market_for_symbol(symbol: str) -> str:
    value = symbol.strip().upper()
    if value.endswith(".OL"):
        return "Oslo"
    if value.endswith(".ST"):
        return "Sweden"
    if value.endswith(".CO"):
        return "Denmark"
    if value.endswith(".HE"):
        return "Finland"
    if value.endswith(".IC"):
        return "Iceland"
    if value.endswith(".AS"):
        return "Netherlands"
    if value.endswith(".BR"):
        return "Belgium"
    if value.endswith(".DE"):
        return "Germany"
    if value.endswith(".L"):
        return "UK"
    if value.endswith(".MI"):
        return "Italy"
    if value.endswith(".PA"):
        return "France"
    if value.endswith(".SW"):
        return "Switzerland"
    return "International"


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
                status text default 'draft',
                curator_note text default '',
                source text default 'manual',
                created_at text not null,
                updated_at text
            );

            create table if not exists peer_group_items (
                group_key text not null,
                symbol text not null,
                role text default 'peer',
                market text default '',
                note text default '',
                source text default 'manual',
                created_at text not null,
                updated_at text,
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
                confidence text default 'single-provider',
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
        ensure_peer_group_schema(con)
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
        existing = con.execute("select source from peer_groups where group_key = ?", (group_key,)).fetchone()
        can_update = existing is None or existing["source"] != "manual"
        if can_update:
            con.execute(
                """
                insert into peer_groups(group_key, name, description, status, curator_note, source, created_at, updated_at)
                values (?, ?, ?, ?, ?, ?, ?, ?)
                on conflict(group_key) do update set
                    name = excluded.name,
                    description = excluded.description,
                    status = excluded.status,
                    curator_note = excluded.curator_note,
                    source = excluded.source,
                    updated_at = excluded.updated_at
                """,
                (
                    group_key,
                    group["name"],
                    group["description"],
                    group.get("status", "draft"),
                    group.get("curator_note", "Seeded for curation; keep draft until reviewed company-by-company."),
                    group["source"],
                    now,
                    now,
                ),
            )
            con.execute("delete from peer_group_items where group_key = ?", (group_key,))
        else:
            continue

        for item in group["items"]:
            if isinstance(item, dict):
                symbol = item["symbol"]
                role = item.get("role", "international peer")
                market = item.get("market", "")
                note = item.get("note", "")
            else:
                symbol, role, market = item
                note = "Seeded focus company." if normalize_peer_role(role, market) == "focus company" else "Seeded peer; review fit before relying on the group."
            normalized = normalize_peer_symbol(symbol, role, market)
            normalized_role = normalize_peer_role(role, market)
            con.execute(
                """
                insert or ignore into tickers(symbol, name, source, created_at)
                values (?, ?, ?, ?)
                """,
                (normalized, normalized.replace(".OL", ""), "peer-group seed", now),
            )
            con.execute(
                """
                insert into peer_group_items(group_key, symbol, role, market, note, source, created_at, updated_at)
                values (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (group_key, normalized, normalized_role, market, note, group["source"], now, now),
            )


def table_columns(con: sqlite3.Connection, table: str) -> set[str]:
    return {row["name"] for row in con.execute(f"pragma table_info({table})").fetchall()}


def ensure_column(con: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    if column not in table_columns(con, table):
        con.execute(f"alter table {table} add column {column} {definition}")


def ensure_peer_group_schema(con: sqlite3.Connection) -> None:
    ensure_column(con, "peer_groups", "status", "text default 'draft'")
    ensure_column(con, "peer_groups", "curator_note", "text default ''")
    ensure_column(con, "peer_groups", "updated_at", "text")
    ensure_column(con, "peer_group_items", "note", "text default ''")
    ensure_column(con, "peer_group_items", "updated_at", "text")
    now = utc_now()
    con.execute("update peer_groups set status = 'draft' where status is null or status = ''")
    con.execute("update peer_groups set updated_at = coalesce(updated_at, created_at, ?) where updated_at is null", (now,))
    con.execute(
        """
        update peer_groups
        set curator_note = 'Seeded for curation; keep draft until reviewed company-by-company.'
        where source = 'manual seed' and (curator_note is null or curator_note = '')
        """
    )
    con.execute(
        """
        update peer_group_items
        set role = case
            when role = 'focus' then 'focus company'
            when role = 'peer' and lower(market) = 'oslo' then 'Oslo peer'
            when role = 'peer' and lower(market) = 'nordic' then 'Nordic peer'
            when role = 'peer' then 'international peer'
            else role
        end
        where role in ('focus', 'peer')
        """
    )
    con.execute("update peer_group_items set updated_at = coalesce(updated_at, created_at, ?) where updated_at is null", (now,))
    con.execute(
        """
        update peer_group_items
        set note = case
            when role in ('focus company', 'focus') then 'Focus company for this peer group.'
            else 'Seeded peer candidate; document business fit, geography, and data gaps before promoting the group.'
        end
        where source = 'manual seed' and (note is null or note = '')
        """
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
        "priceHistory": fetch_yfinance_price_history(ticker, current_price, info.get("currency") or "NOK", now),
        "newswebUrl": f"https://newsweb.oslobors.no/search?query={urllib.parse.quote(symbol.replace('.OL', ''))}",
        "tradingViewSearchUrl": f"https://www.tradingview.com/search/?query={urllib.parse.quote(symbol.replace('.OL', ''))}",
    }
    return payload


def finite_float(value) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    numeric = float(value)
    return numeric if math.isfinite(numeric) else None


def history_index_date(index_value) -> str | None:
    if index_value is None:
        return None
    if hasattr(index_value, "date"):
        return index_value.date().isoformat()
    return str(index_value)[:10]


def fetch_yfinance_price_history(ticker, current_price: float | None, currency: str, fetched_at: str) -> dict:
    base = {
        "source": "Yahoo Finance via yfinance",
        "window": "1y daily close",
        "fetchedAt": fetched_at,
        "currency": currency,
        "confidence": "missing",
        "limitations": "Open/free historical prices are delayed and may include gaps or adjustments; verify against exchange or primary data.",
    }
    try:
        history = ticker.history(period="1y", interval="1d", auto_adjust=False)
    except Exception as exc:
        return {**base, "status": "unavailable", "error": str(exc)}

    if history is None or getattr(history, "empty", True) or "Close" not in history:
        return {**base, "status": "missing", "observationCount": 0}

    close = history["Close"].dropna()
    values = [value for value in (finite_float(item) for item in close.tolist()) if value is not None and value > 0]
    if not values:
        return {**base, "status": "missing", "observationCount": 0}

    current = finite_float(current_price) or values[-1]
    low = min(values)
    high = max(values)
    range_position = None
    if high > low and current is not None:
        range_position = max(0.0, min(100.0, (current - low) / (high - low) * 100))

    observation_count = len(values)
    return {
        **base,
        "status": "available" if observation_count >= PRICE_HISTORY_MIN_OBSERVATIONS else "thin history",
        "confidence": "screening-grade" if observation_count >= PRICE_HISTORY_MIN_OBSERVATIONS else "low",
        "observationCount": observation_count,
        "current": current,
        "median": median(values),
        "low": low,
        "high": high,
        "rangePositionPct": range_position,
        "percentileInWindow": percentile_position(current, values),
        "firstObservationAt": history_index_date(close.index[0]) if len(close.index) else None,
        "lastObservationAt": history_index_date(close.index[-1]) if len(close.index) else None,
        "pctFromLow": pct_diff(current, low),
        "pctFromHigh": pct_diff(current, high),
    }


def pick_number(info: dict, *keys: str) -> float | None:
    for key in keys:
        value = info.get(key)
        numeric = finite_float(value)
        if numeric is not None:
            return numeric
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
                "single-provider",
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
        "providerRows": len(rows),
        "targetMeanAcrossSources": median(numeric_targets) if numeric_targets else None,
        "analystCountKnown": sum(analyst_counts) if analyst_counts else None,
        "reportedAnalystRefs": sum(analyst_counts) if analyst_counts else None,
        "recommendationSummary": consensus_recommendation_summary(rows),
        "confidence": consensus_confidence(rows),
        "status": "missing" if not rows else ("multi-provider" if len(rows) >= 2 else "single-provider"),
        "note": "Consensus is stored by provider row. Reported analyst counts can overlap across providers and are not deduplicated.",
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
        "providerRows": len(rows),
        "method": "Simple provider-row summary. It is not analyst-count weighted or deduplicated across providers unless source data explicitly supports that.",
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
    payload["historicalContext"] = historical_pricing_context(payload["symbol"], payload)
    payload["ownHistorySignal"] = payload["historicalContext"].get("watchlistSignal")
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
        indicators = {}
        for indicator in card.select(".ind"):
            label_el = indicator.select_one(".ind-label")
            value_el = indicator.select_one(".ind-value")
            if not label_el or not value_el:
                continue
            label = " ".join(label_el.get_text(" ", strip=True).split())
            indicators[label] = value_el.get_text(" ", strip=True)
        rsi14 = parse_float(indicators.get("RSI 14"))
        signals.append(
            {
                "symbol": symbol,
                "ticker": symbol.replace(".OL", ""),
                "signal": signal,
                "section": section,
                "price": price_el.get_text(" ", strip=True) if price_el else None,
                "rsi14": rsi14,
                "indicators": indicators,
                "summary": card_text[:260],
                "url": SCREENER_URL,
            }
        )

    payload = {
        "url": SCREENER_URL,
        "fetchedAt": utc_now(),
        "signals": signals,
        "count": len(signals),
        "sourceReliability": "Parsed from the published RSI14 screener dashboard. This is a link/alert layer only; it does not verify the screener logic.",
    }
    SCREENER_CACHE["payload"] = payload
    SCREENER_CACHE["fetched_at_epoch"] = now_epoch
    result = dict(payload)
    result["cacheStatus"] = "fresh"
    return result


def parse_float(value: str | None) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(str(value).replace("%", "").replace(",", ".").strip())
    except ValueError:
        return None


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
        price_summary = stock_price_summary(fundamental)
        target_summary = consensus_target_summary(fundamental, consensus)
        rating_summary = consensus_rating_summary(consensus)
        rows.append(
            {
                **item,
                "name": item.get("name") or fundamental.get("name") or symbol,
                "sector": item.get("sector") or fundamental.get("sector"),
                "industry": item.get("industry") or fundamental.get("industry"),
                "priceSummary": price_summary,
                "screenerSignal": screener_map.get(symbol),
                "fundamentalHighlight": fundamental_highlight(fundamental),
                "ownHistorySignal": fundamental.get("ownHistorySignal"),
                "peerContext": peer_context_summary(symbol, fundamental),
                "consensusTargetSummary": target_summary,
                "consensusRatingSummary": rating_summary,
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
            "consensus": "Target and recommendation fields are stored by data-provider row. Analyst counts are provider-reported references and may overlap across sources.",
            "watchlist": "The Watchlist is the synthesis view. Each major research tab should expose a compact Watchlist summary field.",
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


def cached_payload_if_present(symbol: str) -> dict | None:
    with connect() as con:
        row = con.execute(
            "select payload from fundamentals_cache where symbol = ?",
            (symbol.strip().upper(),),
        ).fetchone()
    return json.loads(row["payload"]) if row else None


def stock_price_summary(fundamental: dict) -> dict:
    return {
        "price": fundamental.get("price"),
        "currency": fundamental.get("currency") or "NOK",
        "fetchedAt": fundamental.get("fetchedAt"),
        "source": fundamental.get("source") or "Yahoo Finance via yfinance",
        "cacheStatus": fundamental.get("cacheStatus"),
    }


def fundamental_highlight(fundamental: dict) -> dict:
    if not fundamental:
        return {
            "label": "Fundamentals unavailable",
            "detail": "No cached source data for this ticker.",
            "tone": "missing",
        }

    trailing_pe = fundamental.get("trailingPE")
    forward_pe = fundamental.get("forwardPE")
    ev_ebitda = fundamental.get("enterpriseToEbitda")
    price_to_book = fundamental.get("priceToBook")
    dividend_yield = fundamental.get("dividendYield")

    if ev_ebitda and ev_ebitda > 40:
        return {
            "label": "EV/EBITDA source outlier",
            "detail": f"{ev_ebitda:.1f}x; verify before using.",
            "tone": "warning",
        }
    if trailing_pe and forward_pe and forward_pe < trailing_pe * 0.8:
        return {
            "label": "Forward P/E below TTM",
            "detail": f"{trailing_pe:.1f}x TTM / {forward_pe:.1f}x forward.",
            "tone": "info",
        }
    if dividend_yield and dividend_yield >= 5:
        return {
            "label": "Dividend yield stands out",
            "detail": f"{dividend_yield:.1f}%; check payout durability.",
            "tone": "info",
        }
    if price_to_book and price_to_book >= 4:
        return {
            "label": "High P/B multiple",
            "detail": f"{price_to_book:.1f}x book; compare with ROE and growth.",
            "tone": "info",
        }

    details = []
    if trailing_pe:
        details.append(f"P/E {trailing_pe:.1f}x")
    if forward_pe:
        details.append(f"fwd {forward_pe:.1f}x")
    if dividend_yield:
        details.append(f"yield {dividend_yield:.1f}%")
    return {
        "label": "Core multiples",
        "detail": "; ".join(details) if details else "Key multiples missing from source.",
        "tone": "neutral" if details else "missing",
    }


def peer_context_summary(symbol: str, focus: dict) -> dict:
    groups = peer_groups_for_symbol(symbol)
    if not groups:
        return {
            "label": "No peer group",
            "detail": "No relative valuation context configured.",
            "status": "missing",
            "groupName": None,
        }

    group = groups[0]
    group_status = normalize_peer_status(group.get("status", "draft"))
    items = peer_group_items(group["group_key"])
    peer_symbols = [item["symbol"] for item in items if item["symbol"] != symbol]
    peers = [payload for payload in (cached_payload_if_present(item) for item in peer_symbols) if payload]
    metric_candidates = [
        metric_summary(focus, peers, metric)
        for metric in BENCHMARK_METRICS
        if metric["key"] in {"trailingPE", "forwardPE", "priceToBook", "enterpriseToEbitda"}
    ]
    notable = [
        metric
        for metric in metric_candidates
        if metric["focusValue"] is not None and metric["peerMedian"] is not None and metric["peerCount"] >= 2
    ]
    notable.sort(key=lambda metric: abs(metric["vsPeerMedianPct"] or 0), reverse=True)
    if notable:
        metric = notable[0]
        return {
            "label": f"{metric['label']} vs peers",
            "detail": f"{metric['focusValue']:.1f}{metric['unit']} / median {metric['peerMedian']:.1f}{metric['unit']}",
            "vsPeerMedianPct": metric["vsPeerMedianPct"],
            "peerCount": metric["peerCount"],
            "status": group_status,
            "groupName": group["name"],
            "note": peer_status_note(group_status),
            "updatedAt": group.get("updated_at"),
        }

    return {
        "label": f"{group_status.title()} peer group",
        "detail": f"{len(peer_symbols)} peers configured; load Benchmarks for context.",
        "peerCount": len(peer_symbols),
        "status": group_status,
        "groupName": group["name"],
        "note": peer_status_note(group_status),
        "updatedAt": group.get("updated_at"),
    }


def consensus_target_summary(fundamental: dict, consensus: dict) -> dict:
    sources = consensus.get("sources", [])
    target_values = [source.get("target_mean") for source in sources if isinstance(source.get("target_mean"), (int, float))]
    target_lows = [source.get("target_low") for source in sources if isinstance(source.get("target_low"), (int, float))]
    target_highs = [source.get("target_high") for source in sources if isinstance(source.get("target_high"), (int, float))]
    target = consensus.get("targetMeanAcrossSources") or fundamental.get("targetMeanPrice")
    price = fundamental.get("price")
    upside = pct_diff(target, price)
    return {
        "target": target,
        "targetLow": min(target_lows) if target_lows else fundamental.get("targetLowPrice"),
        "targetHigh": max(target_highs) if target_highs else fundamental.get("targetHighPrice"),
        "targetUpsidePct": upside,
        "providerRows": len(target_values),
        "source": fundamental.get("targetPriceSource"),
        "method": fundamental.get("targetPriceMethod"),
    }


def consensus_rating_summary(consensus: dict) -> dict:
    recommendation = consensus.get("recommendationSummary", {})
    return {
        "label": recommendation.get("label") or "n/a",
        "counts": recommendation.get("counts", {}),
        "providerRows": consensus.get("sourceCount", 0),
        "reportedAnalystRefs": consensus.get("analystCountKnown"),
        "confidence": consensus.get("confidence"),
        "status": consensus.get("status"),
        "method": recommendation.get("method"),
    }


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
            select pg.group_key, pg.name, pg.description, pg.status, pg.curator_note,
                   pg.source, pg.created_at, pg.updated_at
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
            select pgi.group_key, pgi.symbol, pgi.role, pgi.market, pgi.note,
                   pgi.source, pgi.created_at, pgi.updated_at,
                   t.name, t.sector, t.industry
            from peer_group_items pgi
            left join tickers t on t.symbol = pgi.symbol
            where pgi.group_key = ?
            order by case when pgi.role in ('focus company', 'focus') then 0 else 1 end, pgi.symbol
            """,
            (group_key,),
        ).fetchall()
    return rows_to_dicts(rows)


def peer_status_note(status: str) -> str:
    if status == "trusted":
        return "Trusted peer group, still descriptive and dependent on source coverage."
    if status == "reviewed":
        return "Reviewed peer group; metrics remain screening context, not a valuation verdict."
    return "Draft peer group. Review peers company-by-company before relying on this context."


def peer_confidence(group: dict) -> tuple[str, str]:
    status = normalize_peer_status(group.get("status", "draft"))
    if status == "trusted":
        return (
            "trusted peer group",
            "Peer fit is marked trusted locally, but yfinance coverage and sector-specific gaps still limit conclusions.",
        )
    if status == "reviewed":
        return (
            "reviewed peer group",
            "Peer fit has been reviewed locally; metrics remain descriptive and depend on source quality.",
        )
    return (
        "draft peer group",
        "Peer group is a draft seed or manual edit. Use as a research prompt until reviewed company-by-company.",
    )


def draft_peer_candidates(focus_symbol: str, focus_payload: dict, limit: int = 8) -> list[dict]:
    focus_symbol = focus_symbol.strip().upper()
    focus_industry = (focus_payload.get("industry") or "").strip().lower()
    focus_sector = (focus_payload.get("sector") or "").strip().lower()
    with connect() as con:
        rows = rows_to_dicts(
            con.execute(
                """
                select distinct t.symbol, t.name, t.sector, t.industry
                from tickers t
                where t.symbol <> ?
                order by
                  case
                    when t.symbol like '%.OL' then 0
                    when t.symbol like '%.ST' or t.symbol like '%.CO' or t.symbol like '%.HE' or t.symbol like '%.IC' then 1
                    when t.symbol like '%.DE' or t.symbol like '%.PA' or t.symbol like '%.MI' or t.symbol like '%.L' or t.symbol like '%.AS' or t.symbol like '%.SW' or t.symbol like '%.BR' then 2
                    else 3
                  end,
                  t.symbol
                """,
                (focus_symbol,),
            ).fetchall()
        )

    candidates = []
    seen = set()
    for row in rows:
        industry = (row.get("industry") or "").strip().lower()
        sector = (row.get("sector") or "").strip().lower()
        match_type = ""
        if focus_industry and industry and focus_industry == industry:
            match_type = "same Yahoo/yfinance industry"
        elif focus_sector and sector and focus_sector == sector:
            match_type = "same Yahoo/yfinance sector"
        if not match_type or row["symbol"] in seen:
            continue
        seen.add(row["symbol"])
        candidates.append(
            {
                "symbol": row["symbol"],
                "role": peer_role_for_symbol(row["symbol"]),
                "market": peer_market_for_symbol(row["symbol"]),
                "note": f"Auto-suggested from local ticker database: {match_type}. Review business fit, scale, geography, and sector-specific KPIs before promoting.",
            }
        )
        if len(candidates) >= limit:
            break
    return candidates


def create_or_reuse_draft_peer_group(symbol: str, refresh: bool = False) -> dict:
    symbol = normalize_symbol(symbol)
    existing_groups = peer_groups_for_symbol(symbol)
    if existing_groups:
        group = existing_groups[0]
        return {
            "ok": True,
            "action": "reused",
            "symbol": symbol,
            "groupKey": group["group_key"],
            "group": {**group, "items": peer_group_items(group["group_key"])},
            "message": "Symbol already belongs to a peer group; reusing existing context.",
        }

    focus = cached_fundamental(symbol, refresh=refresh, assume_oslo=False)
    group_key = normalize_group_key(f"{symbol}-draft-peers")
    industry_or_sector = focus.get("industry") or focus.get("sector") or "company"
    name = f"{industry_or_sector} - {symbol} draft peers"
    description = (
        f"Draft peer group for {symbol}. Candidates are generated from local ticker metadata and yfinance "
        "sector/industry matches where available."
    )
    curator_note = (
        "Backend-assisted draft only. Review peers in order of Oslo, Nordic, European, then international fit. "
        "Do not promote until business model, segment mix, scale, source quality, and missing sector KPIs are checked."
    )
    focus_item = {
        "symbol": symbol,
        "role": "focus company",
        "market": peer_market_for_symbol(symbol),
        "note": "Focus company. Draft group created because no existing peer group contained this symbol.",
    }
    items = [focus_item, *draft_peer_candidates(symbol, focus)]
    now = utc_now()
    with connect() as con:
        con.execute(
            """
            insert into peer_groups(group_key, name, description, status, curator_note, source, created_at, updated_at)
            values (?, ?, ?, ?, ?, ?, ?, ?)
            on conflict(group_key) do update set
                name = excluded.name,
                description = excluded.description,
                status = excluded.status,
                curator_note = excluded.curator_note,
                source = excluded.source,
                updated_at = excluded.updated_at
            """,
            (group_key, name, description, "draft", curator_note, "backend draft/yfinance metadata", now, now),
        )
        con.execute("delete from peer_group_items where group_key = ?", (group_key,))
        for item in items:
            con.execute(
                """
                insert or ignore into tickers(symbol, name, source, created_at)
                values (?, ?, ?, ?)
                """,
                (item["symbol"], item["symbol"].replace(".OL", ""), "backend draft peer group", now),
            )
            con.execute(
                """
                insert into peer_group_items(group_key, symbol, role, market, note, source, created_at, updated_at)
                values (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    group_key,
                    item["symbol"],
                    item["role"],
                    item["market"],
                    item["note"],
                    "backend draft/yfinance metadata",
                    now,
                    now,
                ),
            )

    group = peer_groups_for_symbol(symbol)[0]
    return {
        "ok": True,
        "action": "created",
        "symbol": symbol,
        "groupKey": group_key,
        "candidateCount": max(0, len(items) - 1),
        "group": {**group, "items": peer_group_items(group_key)},
        "message": "Created a draft peer group from screening-grade local/yfinance metadata.",
    }


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


def own_history_observation(row) -> dict:
    return {"payload": json.loads(row["payload"]), "fetched_at": row["fetched_at"]}


def own_history_summary(symbol: str, current_payload: dict | None = None) -> dict:
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
    observations = [own_history_observation(row) for row in rows]
    if current_payload:
        current_fetched_at = current_payload.get("fetchedAt")
        if current_fetched_at and current_fetched_at not in {item["fetched_at"] for item in observations}:
            observations.append({"payload": current_payload, "fetched_at": current_fetched_at})
    observations.sort(key=lambda item: item["fetched_at"] or "")
    payloads = [item["payload"] for item in observations]
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
        "snapshotCount": len(observations),
        "firstSnapshotAt": observations[0]["fetched_at"] if observations else None,
        "lastSnapshotAt": observations[-1]["fetched_at"] if observations else None,
        "metrics": summaries,
        "status": "insufficient history" if len(observations) < SNAPSHOT_HISTORY_MIN_OBSERVATIONS else "usable history",
        "requirement": (
            "Own-history valuation context needs several dated observations. "
            "Local snapshots start accumulating when fundamentals are refreshed."
        ),
    }


def metric_gap_label(metric: dict) -> str | None:
    gap = metric.get("vsHistoryMedianPct")
    if gap is None:
        return None
    direction = "above" if gap >= 0 else "below"
    return f"{metric['label']} {direction} own-history median"


def own_snapshot_signal(history: dict) -> dict | None:
    metrics = []
    for metric in history.get("metrics", []):
        if metric.get("key") not in OWN_HISTORY_METRIC_KEYS:
            continue
        if metric.get("observations", 0) < SNAPSHOT_HISTORY_MIN_OBSERVATIONS:
            continue
        gap = metric.get("vsHistoryMedianPct")
        if gap is None or abs(gap) < 25:
            continue
        metrics.append(metric)
    if not metrics:
        return None

    metric = sorted(metrics, key=lambda item: abs(item.get("vsHistoryMedianPct") or 0), reverse=True)[0]
    return {
        "status": "available",
        "label": metric_gap_label(metric),
        "detail": (
            f"{metric['current']:.1f}{metric['unit']} vs median "
            f"{metric['historyMedian']:.1f}{metric['unit']} across {metric['observations']} local snapshots."
        ),
        "metricKey": metric["key"],
        "magnitude": abs(metric.get("vsHistoryMedianPct") or 0),
        "source": "local fundamentals snapshots",
        "confidence": "screening-grade",
        "limitations": "Local snapshots are only as good as prior refresh coverage and Yahoo/yfinance source quality.",
    }


def price_window_signal(price_window: dict | None) -> dict | None:
    if not price_window:
        return None
    observations = price_window.get("observationCount") or 0
    if observations < PRICE_HISTORY_MIN_OBSERVATIONS:
        return None
    position = price_window.get("rangePositionPct")
    percentile = price_window.get("percentileInWindow")
    if position is None or percentile is None:
        return None

    label = None
    magnitude = 0.0
    if position >= 90 or percentile >= 90:
        label = "Near 52-week high"
        magnitude = max(position, percentile) - 50
    elif position <= 10 or percentile <= 10:
        label = "Near 52-week low"
        magnitude = 50 - min(position, percentile)
    elif percentile >= 85:
        label = "High 52-week price percentile"
        magnitude = percentile - 50
    elif percentile <= 15:
        label = "Low 52-week price percentile"
        magnitude = 50 - percentile

    if not label:
        return None

    return {
        "status": "available",
        "label": label,
        "detail": (
            f"{percentile:.0f}th percentile of {observations} daily closes; "
            f"range position {position:.0f}%."
        ),
        "metricKey": "price",
        "magnitude": magnitude,
        "source": price_window.get("source"),
        "confidence": price_window.get("confidence"),
        "limitations": price_window.get("limitations"),
    }


def historical_pricing_context(symbol: str, payload: dict) -> dict:
    price_window = payload.get("priceHistory")
    snapshot_history = own_history_summary(symbol, current_payload=payload)
    metric_rows = []
    for metric in snapshot_history.get("metrics", []):
        history_median = metric.get("historyMedian")
        current = metric.get("current")
        metric_rows.append(
            {
                **metric,
                "vsHistoryMedianPct": pct_diff(current, history_median),
                "source": "local fundamentals snapshots",
                "confidence": (
                    "screening-grade"
                    if metric.get("observations", 0) >= SNAPSHOT_HISTORY_MIN_OBSERVATIONS
                    else "insufficient observations"
                ),
            }
        )
    snapshot_history["metrics"] = metric_rows

    signals = [signal for signal in [price_window_signal(price_window), own_snapshot_signal(snapshot_history)] if signal]
    signals.sort(key=lambda item: item.get("magnitude") or 0, reverse=True)
    has_price_context = (price_window or {}).get("observationCount", 0) >= PRICE_HISTORY_MIN_OBSERVATIONS
    has_snapshot_context = snapshot_history.get("snapshotCount", 0) >= SNAPSHOT_HISTORY_MIN_OBSERVATIONS
    has_context = has_price_context or has_snapshot_context
    if signals:
        watchlist_signal = signals[0]
    elif has_context:
        watchlist_signal = {
            "status": "no watchlist signal",
            "label": "No large own-history gap",
            "detail": "Enough history for context, but no price or multiple gap crossed the Watchlist signal threshold.",
            "source": "Yahoo/yfinance and local fundamentals snapshots",
            "confidence": "screening-grade" if has_price_context else "local snapshots",
        }
    else:
        watchlist_signal = {
            "status": "insufficient history",
            "label": "Own-history signal unavailable",
            "detail": "Requires enough daily prices or local fundamentals snapshots before surfacing in Watchlist.",
            "source": "Yahoo/yfinance and local fundamentals snapshots",
            "confidence": "insufficient observations",
        }

    return {
        "symbol": symbol,
        "status": "available" if has_context else "insufficient history",
        "priceWindow": price_window,
        "snapshotHistory": snapshot_history,
        "watchlistSignal": watchlist_signal,
        "requirements": {
            "priceWindowMinimumObservations": PRICE_HISTORY_MIN_OBSERVATIONS,
            "snapshotMinimumObservations": SNAPSHOT_HISTORY_MIN_OBSERVATIONS,
        },
        "policy": (
            "Historical context is descriptive only. It compares current values with own price history and local "
            "fundamentals snapshots without producing cheap, expensive, buy, sell, or hold conclusions."
        ),
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
                row["peerNote"] = item.get("note", "")
                row["peerSource"] = item.get("source", "")
                rows.append(row)
            except Exception as exc:
                errors.append({"symbol": item["symbol"], "error": str(exc)})

        focus = next((row for row in rows if row["symbol"] == symbol), None)
        if focus is None:
            try:
                focus = cached_fundamental(symbol, refresh=refresh, assume_oslo=False)
                focus["peerRole"] = "focus company"
                focus["peerMarket"] = "Oslo"
                focus["peerNote"] = "Focus company was not present in the selected group."
                rows.append(focus)
            except Exception as exc:
                errors.append({"symbol": symbol, "error": str(exc)})
                focus = {"symbol": symbol}

        peers = [row for row in rows if row.get("symbol") != symbol]
        confidence, confidence_reason = peer_confidence(group)
        results.append(
            {
                **group,
                "items": rows,
                "configuredItems": items,
                "errors": errors,
                "metricSummaries": [metric_summary(focus, peers, metric) for metric in BENCHMARK_METRICS],
                "coverage": {
                    "configuredPeers": len(items),
                    "loadedRows": len(rows),
                    "errors": len(errors),
                },
                "confidence": confidence,
                "confidenceReason": confidence_reason,
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
        if parsed.path == "/api/peer-groups":
            return self.handle_peer_group_post()
        if parsed.path == "/api/peer-groups/draft":
            return self.handle_peer_group_draft_post()
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
        include_items = qs.get("includeItems", ["0"])[0] == "1"
        with connect() as con:
            if symbol:
                groups = peer_groups_for_symbol(normalize_symbol(symbol))
            else:
                groups = rows_to_dicts(con.execute("select * from peer_groups order by name").fetchall())
        if include_items:
            for group in groups:
                group["items"] = peer_group_items(group["group_key"])
        send_json(self, {"groups": groups})

    def handle_peer_group_post(self) -> None:
        body = get_json_body(self)
        name = (body.get("name") or "").strip()
        group_key = normalize_group_key(body.get("groupKey") or name)
        if not name:
            return send_json(self, {"error": "name is required"}, HTTPStatus.BAD_REQUEST)

        status = normalize_peer_status(body.get("status", "draft"))
        description = (body.get("description") or "").strip()
        curator_note = (body.get("curatorNote") or body.get("curator_note") or "").strip()
        now = utc_now()
        items = []
        seen_symbols = set()
        for raw_item in body.get("items", []):
            raw_symbol = (raw_item.get("symbol") or "").strip()
            if not raw_symbol:
                continue
            role = normalize_peer_role(raw_item.get("role", ""), raw_item.get("market", ""))
            market = (raw_item.get("market") or "").strip()
            symbol = normalize_peer_symbol(raw_symbol, role, market)
            if not symbol or symbol in seen_symbols:
                continue
            seen_symbols.add(symbol)
            items.append(
                {
                    "symbol": symbol,
                    "role": role,
                    "market": market,
                    "note": (raw_item.get("note") or "").strip(),
                }
            )
        if not items:
            return send_json(self, {"error": "at least one peer-group item is required"}, HTTPStatus.BAD_REQUEST)

        with connect() as con:
            con.execute(
                """
                insert into peer_groups(group_key, name, description, status, curator_note, source, created_at, updated_at)
                values (?, ?, ?, ?, ?, ?, ?, ?)
                on conflict(group_key) do update set
                    name = excluded.name,
                    description = excluded.description,
                    status = excluded.status,
                    curator_note = excluded.curator_note,
                    source = 'manual',
                    updated_at = excluded.updated_at
                """,
                (group_key, name, description, status, curator_note, "manual", now, now),
            )
            con.execute("delete from peer_group_items where group_key = ?", (group_key,))
            for item in items:
                con.execute(
                    """
                    insert or ignore into tickers(symbol, name, source, created_at)
                    values (?, ?, ?, ?)
                    """,
                    (item["symbol"], item["symbol"].replace(".OL", ""), "manual/peer-group", now),
                )
                con.execute(
                    """
                    insert into peer_group_items(group_key, symbol, role, market, note, source, created_at, updated_at)
                    values (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        group_key,
                        item["symbol"],
                        item["role"],
                        item["market"],
                        item["note"],
                        "manual",
                        now,
                        now,
                    ),
                )
        send_json(self, {"ok": True, "groupKey": group_key, "status": status, "itemCount": len(items)})

    def handle_peer_group_draft_post(self) -> None:
        body = get_json_body(self)
        symbol = normalize_symbol(body.get("symbol", ""))
        if not symbol:
            return send_json(self, {"error": "symbol is required"}, HTTPStatus.BAD_REQUEST)
        refresh = bool(body.get("refresh"))
        try:
            send_json(self, create_or_reuse_draft_peer_group(symbol, refresh=refresh))
        except Exception as exc:
            return send_json(self, {"error": str(exc)}, HTTPStatus.BAD_GATEWAY)

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
            "verification": "Fetched successfully from GitHub Pages during setup. The page is treated as an embedded external artifact and is not edited by this MVP. Watchlist RSI14 context parses ticker, signal, and RSI 14 card values from the published page.",
            "limitations": "Only cards present in the published dashboard are available to this app. A published latest.csv or equivalent full dataset is still needed for RSI14 coverage across all 111 screened stocks.",
        },
        "yfinance": {
            "use": "Open/free Yahoo Finance data for price, 52-week daily price history, multiples, and analyst target fields where available.",
            "limitations": "Delayed, rate-limited, not guaranteed complete. Historical prices may include gaps or adjustment differences. Target-price and recommendation fields are labeled as Yahoo/yfinance only and should be verified against other consensus sources.",
        },
        "historicalContext": {
            "use": "Fundamentals now shows descriptive own-history context from Yahoo/yfinance 52-week daily closes and local dated fundamentals snapshots.",
            "limitations": "Watchlist own-history signals require minimum observation counts. Multiple history depends on repeated local refreshes and is not a sector, peer, or valuation verdict.",
        },
        "benchmarks": {
            "use": "Editable peer groups plus cached yfinance metrics for descriptive relative context. New symbols can create backend-assisted draft groups from local/yfinance sector metadata.",
            "limitations": "No cheap/expensive verdict is produced. Draft/reviewed/trusted are local peer-curation markers only. Backend-assisted groups are draft only and require business-model review; own-history context starts accumulating from local refresh snapshots.",
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
