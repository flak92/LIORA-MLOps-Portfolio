"""Download Binance USDS-M 1m klines into QuantConnect Lean minute-trade ZIPs.

Keyless public API, stdlib only. The unit of work is one full UTC day = one ZIP; days whose ZIP already exists are
skipped, so the same command performs the initial backfill and any later top-up.

Output tree (Lean-exact):
  store_raw_1m/cryptofuture/binance/minute/<symbol>/YYYYMMDD_trade.zip
    -> YYYYMMDD_<symbol>_minute_trade_perp.csv
       rows: offset_ms_from_utc_midnight,open,high,low,close,volume  (ascending)

Volume is BASE volume (klines column 5), not quote turnover.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime

from . import config
from .lean import MILLISECONDS_PER_DAY, MINUTES_PER_DAY, is_full_utc_day, lean_day_zip_name, write_lean_zip


def to_utc_day(epoch_ms: int) -> str:
    return datetime.fromtimestamp(epoch_ms / config.MILLISECONDS_PER_SECOND, tz=UTC).strftime("%Y-%m-%d")


def fetch_klines(params: dict, retries: int = 6) -> list[list]:
    url = f"{config.BINANCE_KLINE_URL}?{urllib.parse.urlencode(params)}"
    backoff = 1.0
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": config.USER_AGENT})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            if e.code in (418, 429) and attempt < retries - 1:  # rate limit / ban
                time.sleep(max(backoff, float(e.headers.get("Retry-After", 0) or 0)))
                backoff *= 2
                continue
            if attempt == retries - 1:
                raise
            time.sleep(backoff)
            backoff *= 2
        except (urllib.error.URLError, TimeoutError):
            if attempt == retries - 1:
                raise
            time.sleep(backoff)
            backoff *= 2


def fetch_oldest_candle_ms(symbol: str) -> int:
    """Epoch ms of the oldest 1m candle Binance serves for this symbol."""
    batch = fetch_klines({"symbol": symbol, "interval": config.SOURCE_CANDLE_INTERVAL,
                  "startTime": 0, "limit": 1})
    return int(batch[0][0])


def fetch_day(symbol: str, day_ms: int) -> list[tuple]:
    """All 1m candles of one UTC day as (offset_ms, o, h, l, c, base_volume)."""
    batch = fetch_klines(
        {
            "symbol": symbol,
            "interval": config.SOURCE_CANDLE_INTERVAL,
            "startTime": day_ms,
            "endTime": day_ms + MILLISECONDS_PER_DAY - 1,
            "limit": config.BINANCE_KLINE_REQUEST_LIMIT,
        }
    )
    return [(int(row[0]) - day_ms, row[1], row[2], row[3], row[4], row[5]) for row in batch]


def main() -> int:
    args = config.build_ticker_parser("Binance USDS-M 1m klines -> Lean minute-trade ZIPs").parse_args()
    tickers = config.parse_tickers(args.tickers)

    now = datetime.now(tz=UTC)
    end_ms = int(now.replace(hour=0, minute=0, second=0, microsecond=0).timestamp() * config.MILLISECONDS_PER_SECOND)
    start_ms = config.DATA_WINDOW_START_MS

    print(f"window [{to_utc_day(start_ms)} .. {to_utc_day(end_ms)}) — probing listings:", flush=True)
    for ticker in tickers:
        oldest = fetch_oldest_candle_ms(config.symbol(ticker))
        listing_covers_window = oldest <= start_ms
        print(f"  {config.symbol(ticker):9} oldest candle {to_utc_day(oldest)}  {'ok' if listing_covers_window else 'AFTER WINDOW START'}", flush=True)
        if not listing_covers_window:
            raise SystemExit(f"{config.symbol(ticker)}: history starts after {to_utc_day(start_ms)} — basket rule broken")

    total_days = (end_ms - start_ms) // MILLISECONDS_PER_DAY
    for ticker in tickers:
        symbol = config.symbol(ticker)
        out_dir = config.raw_symbol_dir(ticker, "binance")
        written = skipped = 0
        day_ms = start_ms
        t0 = time.time()
        while day_ms < end_ms:
            day = datetime.fromtimestamp(day_ms / config.MILLISECONDS_PER_SECOND, tz=UTC).strftime("%Y%m%d")
            if (out_dir / lean_day_zip_name(day)).exists():
                skipped += 1
            else:
                rows = fetch_day(symbol, day_ms)
                # every day of the window is post-listing (probed above), so a short day is a truncated response
                if not is_full_utc_day(rows):
                    raise SystemExit(
                        f"{symbol} {day}: {len(rows)} of {MINUTES_PER_DAY} minutes — "
                        "incomplete response for a post-listing day, retry the download"
                    )
                write_lean_zip(out_dir, symbol, day, rows)
                written += 1
                if written % 200 == 0:
                    print(f"  {symbol}: {written + skipped}/{total_days} days ({time.time() - t0:.0f}s)", flush=True)
                time.sleep(config.BINANCE_REQUEST_DELAY_SECONDS)
            day_ms += MILLISECONDS_PER_DAY
        print(f"{symbol}: {written} days downloaded, {skipped} already present ({time.time() - t0:.0f}s)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
