"""Habit tracking logic: check-ins and streak calculation."""
from __future__ import annotations

from datetime import date, timedelta


def check_in(data: dict, name: str, day: date) -> bool:
    """Record a check-in. Returns False if the day was already recorded."""
    days = data["habits"].setdefault(name, [])
    iso = day.isoformat()
    if iso in days:
        return False
    days.append(iso)
    days.sort()
    return True


def current_streak(days: list[str], today: date) -> int:
    """Consecutive days ending today (or yesterday, so an unfinished day keeps the streak)."""
    done = {date.fromisoformat(d) for d in days}
    cursor = today if today in done else today - timedelta(days=1)
    streak = 0
    while cursor in done:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def longest_streak(days: list[str]) -> int:
    parsed = sorted({date.fromisoformat(d) for d in days})
    best = run = 0
    prev = None
    for d in parsed:
        run = run + 1 if prev and d - prev == timedelta(days=1) else 1
        best = max(best, run)
        prev = d
    return best
