"""The QuantConnect Lean minute-trade format — the data layer's one external-format boundary.

Lean's vocabulary lives here: the day-ZIP and CSV names, the full-UTC-day predicate, the ZIP writer and the parser
that reads a ZIP back. The downloaders hand it venue-neutral rows, ingest reads the tree it writes through its
parser, and the tree above the file name (`cryptofuture/<venue>/minute/<symbol>/`) comes from config.py.
"""

import csv
import io
import re
import zipfile
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

from .config import MILLISECONDS_PER_DAY, MILLISECONDS_PER_MINUTE, MILLISECONDS_PER_SECOND

MINUTES_PER_DAY = MILLISECONDS_PER_DAY // MILLISECONDS_PER_MINUTE

LEAN_DAY_ZIP_GLOB = "*_trade.zip"
LEAN_DAY_ZIP_NAME_PATTERN = re.compile(r"^(\d{8})_trade\.zip$")


def load_lean_day_zip_paths(zip_dir: Path) -> list[Path]:
    """Every day ZIP of one symbol directory, in day order — the one enumeration of a raw leaf.

    The grammar is the filter: a name the pattern does not match is not a day of this tree, so a
    foreign `*_trade.zip` is invisible to every stage rather than to some of them.
    """
    matched = ((LEAN_DAY_ZIP_NAME_PATTERN.match(path.name), path) for path in zip_dir.glob(LEAN_DAY_ZIP_GLOB))
    return [path for _, path in sorted((match.group(1), path) for match, path in matched if match)]


def lean_day_zip_name(day: str) -> str:
    """`YYYYMMDD_trade.zip` — one UTC calendar day."""
    return f"{day}_trade.zip"


def lean_day_csv_name(symbol: str, day: str) -> str:
    """`YYYYMMDD_<symbol lowercase>_minute_trade_perp.csv` — the single entry inside the day ZIP."""
    return f"{day}_{symbol.lower()}_minute_trade_perp.csv"


def is_full_utc_day(rows: list[tuple]) -> bool:
    """Exactly the 1440 minutes of one UTC day, in order, on the 60 000 ms grid."""
    return len(rows) == MINUTES_PER_DAY and all(
        row[0] == i * MILLISECONDS_PER_MINUTE for i, row in enumerate(rows)
    )


def write_lean_zip(out_dir: Path, symbol: str, day: str, rows: list[tuple]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    # a row is (the bar-open offset from UTC midnight in ms, open, high, low, close, volume), written as it came
    body = "\n".join(",".join(str(value) for value in row) for row in rows)
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr(lean_day_csv_name(symbol, day), body)
    (out_dir / lean_day_zip_name(day)).write_bytes(zip_buffer.getvalue())


def utc_midnight_ms(yyyymmdd: str) -> int:
    return int(datetime.strptime(yyyymmdd, "%Y%m%d").replace(tzinfo=UTC).timestamp() * MILLISECONDS_PER_SECOND)


def parse_zip(zip_path: Path) -> Iterator[tuple[int, str, str, str, str, str]]:
    """Yield (epoch_ms, open, high, low, close, volume) from one Lean minute ZIP."""
    midnight_ms = utc_midnight_ms(LEAN_DAY_ZIP_NAME_PATTERN.match(zip_path.name).group(1))
    with zipfile.ZipFile(zip_path) as zip_file:
        with zip_file.open(zip_file.namelist()[0]) as csv_file:
            for row in csv.reader(io.TextIOWrapper(csv_file, encoding="utf-8", newline="")):
                yield (midnight_ms + int(row[0]), row[1], row[2], row[3], row[4], row[5])
