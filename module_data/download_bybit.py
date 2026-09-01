"""Download Bybit Linear USDT 1m klines into QuantConnect Lean minute-trade ZIPs.

Keyless public v5 API, stdlib only; the Binance downloader's twin: one UTC day = one ZIP, existing ZIPs skipped; a
pre-listing day is empty (written once, skipped forever), the listing day may be partial, every later day must be
complete. The v5 limit is 1000 candles, so a day is two 720-minute windows; the list comes newest-first and is
sorted; rate limiting is retCode 10006.

Output tree (Lean-exact, the same format as the Binance tree):
  store_raw_1m/cryptofuture/bybit/minute/<symbol>/YYYYMMDD_trade.zip
    -> YYYYMMDD_<symbol>_minute_trade_perp.csv
       rows: offset_ms_from_utc_midnight,open,high,low,close,volume  (ascending)

Volume is BASE volume (v5 row column 5), matching the Binance tree.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from . import config
from .lean import (MILLISECONDS_PER_DAY, MINUTES_PER_DAY, is_full_utc_day, lean_day_zip_name,
                   lean_day_zip_paths, write_lean_zip)

KLINE_REQUEST_WINDOW_MS = 720 * config.MILLISECONDS_PER_MINUTE  # half a day fits in one 1000-candle response


def fetch_klines(params: dict, retries: int = 6) -> list[list]:
    url = f"{config.BYBIT_KLINE_URL}?{urllib.parse.urlencode(params)}"
    backoff = 1.0
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": config.USER_AGENT})
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.loads(r.read().decode())
            ret_code = data.get("retCode")
            if ret_code == 0:
                return data.get("result", {}).get("list", [])
            if ret_code == 10006 and attempt < retries - 1:  # rate limit
                time.sleep(backoff)
                backoff *= 2
                continue
            raise RuntimeError(f"Bybit retCode={ret_code} {data.get('retMsg')}")
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
            if attempt == retries - 1:
                raise
            time.sleep(backoff)
            backoff *= 2


def fetch_day(symbol: str, day_ms: int) -> list[tuple]:
    """All 1m candles of one UTC day as ascending (offset_ms, o, h, l, c, base_volume)."""
    rows = []
    for window_start_ms in (day_ms, day_ms + KLINE_REQUEST_WINDOW_MS):
        batch = fetch_klines(
            {
                "category": config.BYBIT_CATEGORY,
                "symbol": symbol,
                "interval": "1",
                "start": window_start_ms,
                "end": window_start_ms + KLINE_REQUEST_WINDOW_MS - 1,
                "limit": config.BYBIT_KLINE_REQUEST_LIMIT,
            }
        )
        rows.extend((int(r[0]) - day_ms, r[1], r[2], r[3], r[4], r[5]) for r in batch)
    return sorted(rows)  # v5 returns newest-first


def load_earliest_traded_day(out_dir: Path) -> str | None:
    """The first day whose ZIP holds a non-empty CSV: evidence that precedes a day is what tells pre-listing from a
    failed request."""
    for zip_path in lean_day_zip_paths(out_dir):
        with zipfile.ZipFile(zip_path) as day_zip:
            entries = day_zip.infolist()
            if entries and entries[0].file_size > 0:
                return zip_path.name[:8]
    return None


def main() -> int:
    args = config.build_ticker_parser("Bybit Linear 1m klines -> Lean minute-trade ZIPs").parse_args()
    tickers = config.parse_tickers(args.tickers)

    now = datetime.now(tz=UTC)
    end_ms = int(now.replace(hour=0, minute=0, second=0, microsecond=0).timestamp() * config.MILLISECONDS_PER_SECOND)
    start_ms = config.DATA_WINDOW_START_MS
    total_days = (end_ms - start_ms) // MILLISECONDS_PER_DAY

    for ticker in tickers:
        symbol = config.symbol(ticker)
        out_dir = config.raw_symbol_dir(ticker, "bybit")
        written = skipped = 0
        earliest = load_earliest_traded_day(out_dir)
        day_ms = start_ms
        t0 = time.time()
        while day_ms < end_ms:
            day = datetime.fromtimestamp(day_ms / config.MILLISECONDS_PER_SECOND, tz=UTC).strftime("%Y%m%d")
            if (out_dir / lean_day_zip_name(day)).exists():
                skipped += 1
            else:
                rows = fetch_day(symbol, day_ms)
                if rows and (earliest is None or day < earliest):
                    earliest = day                       # first traded day may be partial
                elif earliest is not None and day > earliest and not is_full_utc_day(rows):
                    # after the first traded day every day is full; a short answer is a truncated response
                    raise SystemExit(
                        f"bybit {symbol} {day}: {len(rows)} of {MINUTES_PER_DAY} minutes — "
                        "incomplete response after listing, retry the download"
                    )
                write_lean_zip(out_dir, symbol, day, rows)
                written += 1
                if written % 200 == 0:
                    print(f"  bybit {symbol}: {written + skipped}/{total_days} days ({time.time() - t0:.0f}s)", flush=True)
                time.sleep(config.BYBIT_REQUEST_DELAY_SECONDS)
            day_ms += MILLISECONDS_PER_DAY
        print(f"bybit {symbol}: {written} days downloaded, {skipped} already present ({time.time() - t0:.0f}s)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
