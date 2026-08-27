"""Download Binance USDS-M 1m klines into QC Lean minute-trade ZIPs.

Keyless public API, stdlib only, no Docker required. The unit of work is one
full UTC day = one ZIP; days whose ZIP already exists are skipped, so the same
command performs the initial backfill and any later top-up (idempotent).

Before downloading, every symbol's oldest available candle is probed
(startTime=0, limit=1) and the run aborts if any listing is younger than the
window start — equal history for all assets is a hard requirement.

Output tree (Lean-exact, byte-compatible with a Lean data folder):
  raw_downloaded_1m_data/cryptofuture/binance/minute/<symbol>/YYYYMMDD_trade.zip
    -> YYYYMMDD_<symbol>_minute_trade_perp.csv
       rows: offset_ms_from_utc_midnight,open,high,low,close,volume  (ascending)

VOLUME UNITS: klines column 5 = BASE volume (e.g. BTC), not quote turnover.
"""

from __future__ import annotations

import io
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from . import config

DAY_MS = 86_400_000
MILLISECONDS_PER_MINUTE = 60_000
MINUTES_PER_DAY = DAY_MS // MILLISECONDS_PER_MINUTE


def _iso_day(epoch_ms: int) -> str:
    return datetime.fromtimestamp(epoch_ms / 1000, tz=UTC).strftime("%Y-%m-%d")


def _get(params: dict, retries: int = 6) -> list[list]:
    url = f"{config.KLINE_URL}?{urllib.parse.urlencode(params)}"
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
    return []


def probe_oldest(sym: str) -> int:
    """Epoch ms of the oldest 1m candle Binance serves for this symbol."""
    batch = _get({"symbol": sym, "interval": config.SOURCE_CANDLE_INTERVAL,
                  "startTime": 0, "limit": 1})
    if not batch:
        raise SystemExit(f"probe failed: no candles returned for {sym}")
    return int(batch[0][0])


def fetch_day(sym: str, day_ms: int) -> list[tuple]:
    """All 1m candles of one UTC day as (offset_ms, o, h, l, c, base_volume)."""
    batch = _get(
        {
            "symbol": sym,
            "interval": config.SOURCE_CANDLE_INTERVAL,
            "startTime": day_ms,
            "endTime": day_ms + DAY_MS - 1,
            "limit": config.BINANCE_KLINE_REQUEST_LIMIT,
        }
    )
    return [(int(row[0]) - day_ms, row[1], row[2], row[3], row[4], row[5]) for row in batch]


def is_full_utc_day(rows: list[tuple]) -> bool:
    """Exactly the 1440 minutes of one UTC day, in order, with no hole.

    One expression covers completeness, ordering, uniqueness and the exact
    60 000 ms grid from 00:00 to 23:59, because the offsets of a full day are
    the sequence 0, 60000, ... by definition. A short answer is a truncated
    response, and writing it would make the gap permanent: the ZIP exists, so
    the day is skipped forever.
    """
    return len(rows) == MINUTES_PER_DAY and all(
        row[0] == i * MILLISECONDS_PER_MINUTE for i, row in enumerate(rows)
    )


def write_lean_zip(out_dir: Path, sym: str, day: str, rows: list[tuple]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_name = f"{day}_{sym.lower()}_minute_trade_perp.csv"
    body = "\n".join(f"{off},{o},{h},{lo},{c},{v}" for (off, o, h, lo, c, v) in rows)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(csv_name, body)
    # whole or not at all: a truncated ZIP would be skipped forever by the
    # exists() check above and then rejected by ingest
    out = out_dir / f"{day}_trade.zip"
    tmp = out.with_suffix(".zip.tmp")
    tmp.write_bytes(buf.getvalue())
    os.replace(tmp, out)


def main() -> int:
    ap = config.ticker_parser("Binance USDS-M 1m klines -> Lean minute-trade ZIPs")
    ap.add_argument("--days", type=int, default=0, help="only the last N full UTC days (0 = full window)")
    args = ap.parse_args()
    tickers = config.parse_tickers(args.tickers)

    now = datetime.now(tz=UTC)
    end_ms = int(now.replace(hour=0, minute=0, second=0, microsecond=0).timestamp() * 1000)
    start_ms = config.DATA_WINDOW_START_MS if args.days == 0 else end_ms - args.days * DAY_MS

    print(f"window [{_iso_day(start_ms)} .. {_iso_day(end_ms)}) — probing listings:", flush=True)
    for t in tickers:
        oldest = probe_oldest(config.symbol(t))
        ok = oldest <= start_ms
        print(f"  {config.symbol(t):9} oldest candle {_iso_day(oldest)}  {'ok' if ok else 'AFTER WINDOW START'}", flush=True)
        if not ok:
            raise SystemExit(f"{config.symbol(t)}: history starts after {_iso_day(start_ms)} — basket rule broken")

    total_days = (end_ms - start_ms) // DAY_MS
    for t in tickers:
        sym = config.symbol(t)
        out_dir = config.raw_symbol_dir(t)
        written = skipped = 0
        day_ms = start_ms
        t0 = time.time()
        while day_ms < end_ms:
            day = datetime.fromtimestamp(day_ms / 1000, tz=UTC).strftime("%Y%m%d")
            if (out_dir / f"{day}_trade.zip").exists():
                skipped += 1
            else:
                rows = fetch_day(sym, day_ms)
                # the listing probe guarantees every day of the window is
                # post-listing, so anything short of a full day is a truncated
                # response, not a fact about the market
                if not is_full_utc_day(rows):
                    raise SystemExit(
                        f"{sym} {day}: {len(rows)} of {MINUTES_PER_DAY} minutes — "
                        "incomplete response for a post-listing day, retry the download"
                    )
                write_lean_zip(out_dir, sym, day, rows)
                written += 1
                if written % 200 == 0:
                    print(f"  {sym}: {written + skipped}/{total_days} days ({time.time() - t0:.0f}s)", flush=True)
                time.sleep(config.BINANCE_REQUEST_DELAY_SECONDS)
            day_ms += DAY_MS
        print(f"{sym}: {written} days downloaded, {skipped} already present ({time.time() - t0:.0f}s)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
