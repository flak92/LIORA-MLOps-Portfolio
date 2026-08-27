"""Download Bybit Linear USDT 1m klines into QC Lean minute-trade ZIPs.

Keyless public v5 API, stdlib only. Mirrors the Binance downloader: the unit of
work is one full UTC day = one ZIP, existing ZIPs are skipped (idempotent
backfill and top-up with the same command). Because the v5 kline limit is 1000
candles (< 1440), one day is fetched as two 720-minute windows.

Bybit specifics handled here:
  - the kline list comes NEWEST-FIRST -> rows are sorted before the ZIP write;
  - rate limiting is retCode 10006 (not HTTP 429) -> exponential backoff;
  - a day before the symbol's listing returns no rows -> an empty CSV is still
    written, so the day is answered once and skipped forever (pre-listing
    minutes become Binance-only in the fusion, never forward-fills).

Output tree (Lean-exact, same format as the Binance tree):
  raw_downloaded_1m_data/cryptofuture/bybit/minute/<symbol>/YYYYMMDD_trade.zip
    -> YYYYMMDD_<symbol>_minute_trade_perp.csv
       rows: offset_ms_from_utc_midnight,open,high,low,close,volume  (ascending)

VOLUME UNITS: v5 kline row = [start, o, h, l, c, volume(BASE), turnover(USDT)];
column 5 (BASE volume) is written, matching the Binance tree.
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime

from . import config
from .download import DAY_MS, write_lean_zip

WINDOW_MS = 720 * 60_000  # half a day fits in one 1000-candle response


def _get(params: dict, retries: int = 6) -> list[list]:
    url = f"{config.BYBIT_KLINE_URL}?{urllib.parse.urlencode(params)}"
    backoff = 1.0
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": config.USER_AGENT})
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.loads(r.read().decode())
            rc = data.get("retCode")
            if rc == 0:
                return data.get("result", {}).get("list", [])
            if rc == 10006 and attempt < retries - 1:  # rate limit
                time.sleep(backoff)
                backoff *= 2
                continue
            raise RuntimeError(f"Bybit retCode={rc} {data.get('retMsg')}")
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
            if attempt == retries - 1:
                raise
            time.sleep(backoff)
            backoff *= 2
    return []


def fetch_day(sym: str, day_ms: int) -> list[tuple]:
    """All 1m candles of one UTC day as ascending (offset_ms, o, h, l, c, base_volume)."""
    rows = []
    for w0 in (day_ms, day_ms + WINDOW_MS):
        batch = _get(
            {
                "category": config.BYBIT_CATEGORY,
                "symbol": sym,
                "interval": "1",
                "start": w0,
                "end": w0 + WINDOW_MS - 1,
                "limit": config.BYBIT_MAX_LIMIT,
            }
        )
        rows.extend((int(r[0]) - day_ms, r[1], r[2], r[3], r[4], r[5]) for r in batch)
    return sorted(rows)  # v5 returns newest-first


def main() -> int:
    ap = argparse.ArgumentParser(description="Bybit Linear 1m klines -> Lean minute-trade ZIPs")
    ap.add_argument("--tickers", default=",".join(config.TICKERS), help="comma-separated subset")
    ap.add_argument("--days", type=int, default=0, help="only the last N full UTC days (0 = full window)")
    args = ap.parse_args()
    tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]

    now = datetime.now(tz=UTC)
    end_ms = int(now.replace(hour=0, minute=0, second=0, microsecond=0).timestamp() * 1000)
    start_ms = config.START_MS if args.days == 0 else end_ms - args.days * DAY_MS
    total_days = (end_ms - start_ms) // DAY_MS

    for t in tickers:
        sym = config.symbol(t)
        out_dir = config.raw_symbol_dir(t, "bybit")
        written = skipped = 0
        day_ms = start_ms
        t0 = time.time()
        while day_ms < end_ms:
            day = datetime.fromtimestamp(day_ms / 1000, tz=UTC).strftime("%Y%m%d")
            if (out_dir / f"{day}_trade.zip").exists():
                skipped += 1
            else:
                rows = fetch_day(sym, day_ms)
                if not rows and any(p.stat().st_size > 200 for p in out_dir.glob("*_trade.zip")):
                    # the symbol already has traded days -> an empty response is a
                    # transient failure, not a pre-listing day; do not persist a hole
                    raise SystemExit(f"bybit {sym} {day}: empty response after listing — retry the download")
                write_lean_zip(out_dir, sym, day, rows)
                written += 1
                if written % 200 == 0:
                    print(f"  bybit {sym}: {written + skipped}/{total_days} days ({time.time() - t0:.0f}s)", flush=True)
                time.sleep(config.BYBIT_SLEEP_S)
            day_ms += DAY_MS
        print(f"bybit {sym}: {written} days downloaded, {skipped} already present ({time.time() - t0:.0f}s)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
