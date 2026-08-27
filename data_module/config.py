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

# Basket: 10 assets, one uniform market — USDT-margined perpetuals, fused from
# two venues (Binance USDS-M + Bybit Linear). Every asset has Binance 1m
# history starting before START_UTC (probed before every download); Bybit
# joins each symbol whenever its listing starts.
TICKERS = ["BTC", "ETH", "BNB", "XRP", "SOL", "TRX", "DOGE", "ZEC", "LINK", "ADA"]
QUOTE = "USDT"
LEAN_MARKET_FOLDER = "binance"          # Lean market folder name
LEAN_SECURITY_TYPE_FOLDER = "cryptofuture"   # Lean security-type folder name (USDS-M perpetuals)
INTERVAL = "1m"
GRID_STEP_MS = 60_000

# Window start (inclusive, UTC midnight). The window end is always the most
# recent UTC midnight (exclusive): the pipeline only handles full UTC days.
START_UTC = "2021-01-01"
START_MS = int(datetime.fromisoformat(START_UTC).replace(tzinfo=UTC).timestamp() * 1000)

# Public keyless endpoints; both return BASE volume (e.g. BTC), not quote turnover.
KLINE_URL = "https://fapi.binance.com/fapi/v1/klines"
MAX_LIMIT = 1500
SLEEP_S = 0.2
BYBIT_KLINE_URL = "https://api.bybit.com/v5/market/kline"
BYBIT_CATEGORY = "linear"
BYBIT_MAX_LIMIT = 1000          # < 1440 -> one day = 2 windows of 720 minutes
BYBIT_SLEEP_S = 0.1
USER_AGENT = "mlops-portfolio-1m-pipeline/1.0"

VENUES = ("binance", "bybit")

RAW_DIR = REPO_ROOT / "raw_downloaded_1m_data"
DB_PATH = REPO_ROOT / "db" / "research_ohlcv.duckdb"
RESEARCH_ARTIFACTS_DIR = REPO_ROOT / "research_artifacts"
MONITORING_DIR = REPO_ROOT / "monitoring_module"


def symbol(ticker: str) -> str:
    return f"{ticker}{QUOTE}"


def raw_symbol_dir(ticker: str, venue: str = LEAN_MARKET_FOLDER) -> Path:
    """Lean-exact tree: raw_downloaded_1m_data/cryptofuture/<venue>/minute/<symbol>/"""
    return RAW_DIR / LEAN_SECURITY_TYPE_FOLDER / venue / "minute" / symbol(ticker).lower()


def artifact_dir(ticker: str) -> Path:
    """One directory per ticker; inside it one file per stage, named for it."""
    return RESEARCH_ARTIFACTS_DIR / ticker


def canonical_parquet(ticker: str) -> Path:
    return artifact_dir(ticker) / "canonical_1m.parquet"


def ticker_parser(description: str) -> "argparse.ArgumentParser":
    """The one CLI every stage shares: --tickers with the full basket default."""
    ap = argparse.ArgumentParser(description=description)
    ap.add_argument("--tickers", default=",".join(TICKERS), help="comma-separated subset")
    return ap


def parse_tickers(csv: str) -> list[str]:
    return [t.strip().upper() for t in csv.split(",") if t.strip()]
