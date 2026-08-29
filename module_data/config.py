"""Static configuration: the asset basket, time window, endpoints and paths — the plain values every stage reads,
so a fresh clone reconstructs the dataset for the window from the public market APIs."""

from __future__ import annotations

import argparse

from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# USDT-margined perpetuals; Binance USDS-M primary, Bybit Linear failover; every asset has Binance 1m history
# before the window start (probed before every download), Bybit joins whenever its listing starts
# single-asset runtime: this list is the one definition the paths, the fan-out, the compose
# services and the /containers registry derive from — scaling is extending it and adding one
# asset service per ticker under the compose anchor, no logic changes
TICKERS = ["BTC"]
QUOTE_ASSET = "USDT"
LEAN_SECURITY_TYPE_FOLDER = "cryptofuture"   # Lean security-type folder name (USDS-M perpetuals)
SOURCE_CANDLE_INTERVAL = "1m"
MILLISECONDS_PER_SECOND = 1000
MILLISECONDS_PER_MINUTE = 60_000
BYTES_PER_KIBIBYTE = 1024
CANONICAL_GRID_INTERVAL_MS = MILLISECONDS_PER_MINUTE

# Window start (inclusive, UTC midnight). The window end is always the most
# recent UTC midnight (exclusive): the pipeline only handles full UTC days.
DATA_WINDOW_START_UTC = "2021-01-01"
DATA_WINDOW_START_MS = int(datetime.fromisoformat(DATA_WINDOW_START_UTC)
                           .replace(tzinfo=UTC).timestamp() * MILLISECONDS_PER_SECOND)

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

STORE_RAW_1M_DIR = REPO_ROOT / "store_raw_1m"
# DuckDB spills to disk above this ceiling; the thread cap beside it in every connection is determinism
DUCKDB_MEMORY_LIMIT = "4GB"
STORE_ASSETS_ARTIFACTS_DIR = REPO_ROOT / "store_assets_artifacts"
MODULE_MONITORING_DIR = REPO_ROOT / "module_monitoring"
MODULE_MONITORING_DATA_STATUS_JSON_PATH = MODULE_MONITORING_DIR / "data_status.json"


def symbol(ticker: str) -> str:
    return f"{ticker}{QUOTE_ASSET}"


def raw_symbol_dir(ticker: str, venue: str) -> Path:
    """Lean-exact tree: store_raw_1m/cryptofuture/<venue>/minute/<symbol>/"""
    return STORE_RAW_1M_DIR / LEAN_SECURITY_TYPE_FOLDER / venue / "minute" / symbol(ticker).lower()


def artifact_dir(ticker: str) -> Path:
    """One directory per ticker; inside it one file per artifact, named for it."""
    return STORE_ASSETS_ARTIFACTS_DIR / ticker


def research_ohlcv_duckdb(ticker: str) -> Path:
    """The asset's own database — the market object's one home, resident in the asset folder."""
    return artifact_dir(ticker) / f"{ticker}_research_ohlcv.duckdb"


RUN_RECORD_DIR_NAME = "runtime"


def run_records_dir(ticker: str) -> Path:
    """Where the asset's recorded runs live, one directory each."""
    return artifact_dir(ticker) / RUN_RECORD_DIR_NAME


def run_dir(ticker: str, run_id: str) -> Path:
    """One directory per recorded run, beside the artifacts the run produced."""
    return run_records_dir(ticker) / run_id


def build_ticker_parser(description: str) -> argparse.ArgumentParser:
    """The one CLI every stage shares: --tickers with the full basket default."""
    ap = argparse.ArgumentParser(description=description)
    ap.add_argument("--tickers", default=",".join(TICKERS), help="comma-separated subset")
    return ap


def parse_tickers(tickers_csv: str) -> list[str]:
    return [ticker.strip().upper() for ticker in tickers_csv.split(",") if ticker.strip()]


def rounded(x, ndigits: int):
    """round() that tolerates None: the NULL a scan reports when no row qualifies, the None a fold without trades reports."""
    return None if x is None else round(float(x), ndigits)
