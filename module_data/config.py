"""Static configuration: the asset basket, time window, endpoint and paths.

Single source of truth for every stage. All constants are plain values, so a
fresh clone deterministically reconstructs the dataset for the requested time
window from the public market APIs.
"""

from __future__ import annotations

import argparse

from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Basket: one uniform market — USDT-margined perpetuals, one
# primary-failover canonical series built from two venues (Binance USDS-M +
# Bybit Linear). Every asset has Binance 1m
# history starting before DATA_WINDOW_START_UTC (probed before every download);
# Bybit joins each symbol whenever its listing starts.
TICKERS = ["BTC", "ETH", "BNB", "XRP", "SOL", "TRX", "DOGE", "ZEC", "LINK", "ADA"]
QUOTE_ASSET = "USDT"
LEAN_SECURITY_TYPE_FOLDER = "cryptofuture"   # Lean security-type folder name (USDS-M perpetuals)
SOURCE_CANDLE_INTERVAL = "1m"
MILLISECONDS_PER_MINUTE = 60_000
CANONICAL_GRID_INTERVAL_MS = MILLISECONDS_PER_MINUTE

# Window start (inclusive, UTC midnight). The window end is always the most
# recent UTC midnight (exclusive): the pipeline only handles full UTC days.
DATA_WINDOW_START_UTC = "2021-01-01"
DATA_WINDOW_START_MS = int(datetime.fromisoformat(DATA_WINDOW_START_UTC)
                           .replace(tzinfo=UTC).timestamp() * 1000)

# Public keyless endpoints; both return BASE volume (e.g. BTC), not quote turnover.
BINANCE_KLINE_URL = "https://fapi.binance.com/fapi/v1/klines"
BINANCE_KLINE_REQUEST_LIMIT = 1500
BINANCE_REQUEST_DELAY_SECONDS = 0.2
BYBIT_KLINE_URL = "https://api.bybit.com/v5/market/kline"
BYBIT_CATEGORY = "linear"
BYBIT_KLINE_REQUEST_LIMIT = 1000          # < 1440 -> one day = 2 windows of 720 minutes
BYBIT_REQUEST_DELAY_SECONDS = 0.1
USER_AGENT = "mlops-portfolio-1m-pipeline/1.0"

SOURCE_VENUES = ("binance", "bybit")

STORE_RAW_DATA_SS_01_HH_DD_MM_DIR = REPO_ROOT / "store_raw_data_ss-01-hh-dd-MM"
STORE_DB_PATH = REPO_ROOT / "store_db" / "research_ohlcv.duckdb"
# DuckDB spills to disk above this ceiling instead of hitting the allocator on a
# small host; the thread cap next to it in every connection is determinism, not tuning
DUCKDB_MEMORY_LIMIT = "4GB"
STORE_ASSETS_ARTIFACTS_DIR = REPO_ROOT / "store_Assets_artifacts"
MODULE_MONITORING_DIR = REPO_ROOT / "module_monitoring"
MODULE_MONITORING_STATUS_JSON_PATH = MODULE_MONITORING_DIR / "status.json"


def symbol(ticker: str) -> str:
    return f"{ticker}{QUOTE_ASSET}"


def raw_symbol_dir(ticker: str, venue: str) -> Path:
    """Lean-exact tree: store_raw_data_ss-01-hh-dd-MM/cryptofuture/<venue>/minute/<symbol>/"""
    return STORE_RAW_DATA_SS_01_HH_DD_MM_DIR / LEAN_SECURITY_TYPE_FOLDER / venue / "minute" / symbol(ticker).lower()


def artifact_dir(ticker: str) -> Path:
    """One directory per ticker; inside it one file per artifact, named for it."""
    return STORE_ASSETS_ARTIFACTS_DIR / ticker


def ticker_parser(description: str) -> "argparse.ArgumentParser":
    """The one CLI every stage shares: --tickers with the full basket default."""
    ap = argparse.ArgumentParser(description=description)
    ap.add_argument("--tickers", default=",".join(TICKERS), help="comma-separated subset")
    return ap


def parse_tickers(tickers_csv: str) -> list[str]:
    return [t.strip().upper() for t in tickers_csv.split(",") if t.strip()]
