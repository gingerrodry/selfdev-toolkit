"""CSV export/import of habit check-ins (columns: habit,date)."""
from __future__ import annotations

import csv
import io
from datetime import date

from . import habits
from .store import Data

HEADER = ["habit", "date"]


def to_csv(data: Data) -> str:
    """Active habits' check-ins, one row per (habit, date), sorted."""
    buf = io.StringIO(newline="")
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(HEADER)
    for name, days in sorted(habits.active_habits(data).items()):
        for day in sorted(days):
            writer.writerow([name, day])
    return buf.getvalue()


def parse_csv(text: str) -> list[tuple[str, str]]:
    """Parse rows into (habit, iso_date). Raises ValueError naming the first bad line."""
    reader = csv.reader(io.StringIO(text, newline=""))
    rows = list(reader)
    if not rows or [c.strip().lower() for c in rows[0]] != HEADER:
        raise ValueError("line 1: header must be 'habit,date'")
    parsed: list[tuple[str, str]] = []
    for lineno, row in enumerate(rows[1:], start=2):
        if not row:
            continue
        if len(row) != 2 or not row[0].strip():
            raise ValueError(f"line {lineno}: expected 'habit,date'")
        try:
            iso = date.fromisoformat(row[1].strip()).isoformat()
        except ValueError:
            raise ValueError(f"line {lineno}: invalid date '{row[1].strip()}'") from None
        parsed.append((row[0].strip(), iso))
    return parsed


def import_rows(data: Data, rows: list[tuple[str, str]]) -> int:
    """Merge rows into data, skipping existing check-ins. Returns how many were added."""
    added = 0
    for name, iso in rows:
        if habits.check_in(data, name, date.fromisoformat(iso)):
            added += 1
    return added
