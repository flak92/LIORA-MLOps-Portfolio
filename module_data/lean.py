"""The QuantConnect Lean minute-trade format — the data layer's one external-format boundary.

Everything that speaks Lean's vocabulary lives here: the day-ZIP and CSV names,
the full-UTC-day predicate and the ZIP writer. The downloaders hand it
venue-neutral rows, ingest reads the tree it writes, and the tree above the file
name (`cryptofuture/<venue>/minute/<symbol>/`) comes from config.py.
"""

from __future__ import annotations

import io
import os
import re
import zipfile
from pathlib import Path

from .config import MILLISECONDS_PER_MINUTE

MILLISECONDS_PER_DAY = 86_400_000
MINUTES_PER_DAY = MILLISECONDS_PER_DAY // MILLISECONDS_PER_MINUTE

LEAN_DAY_ZIP_GLOB = "*_trade.zip"
LEAN_DAY_ZIP_NAME_PATTERN = re.compile(r"^(\d{8})_trade\.zip$")


def lean_day_zip_name(day: str) -> str:
    """`YYYYMMDD_trade.zip` — one UTC calendar day."""
    return f"{day}_trade.zip"


def lean_day_csv_name(symbol: str, day: str) -> str:
    """`YYYYMMDD_<symbol lowercase>_minute_trade_perp.csv` — the single entry inside the day ZIP."""
    return f"{day}_{symbol.lower()}_minute_trade_perp.csv"


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


def write_lean_zip(out_dir: Path, symbol: str, day: str, rows: list[tuple]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    body = "\n".join(f"{off},{o},{h},{lo},{c},{v}" for (off, o, h, lo, c, v) in rows)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(lean_day_csv_name(symbol, day), body)
    # whole or not at all: a truncated ZIP would be skipped forever by the
    # downloaders' exists() check and then rejected by ingest
    out = out_dir / lean_day_zip_name(day)
    tmp = out.with_suffix(".zip.tmp")
    tmp.write_bytes(buf.getvalue())
    os.replace(tmp, out)
