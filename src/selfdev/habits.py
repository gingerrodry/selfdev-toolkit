"""Habit tracking logic: check-ins and streak calculation."""
from __future__ import annotations

from datetime import date, timedelta

from .store import Data


def check_in(data: Data, name: str, day: date) -> bool:
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


def weekly_summary(data: Data, today: date) -> dict[str, int]:
    """Check-ins per habit over the 7 days ending today (inclusive)."""
    start = today - timedelta(days=6)
    result = {}
    for name, days in data["habits"].items():
        result[name] = sum(1 for d in days if start <= date.fromisoformat(d) <= today)
    return result


def set_target(data: Data, name: str, per_week: int) -> None:
    """Set a weekly goal (1-7 check-ins) for a habit."""
    if not 1 <= per_week <= 7:
        raise ValueError("target must be between 1 and 7 per week")
    data.setdefault("targets", {})[name] = per_week


def remove_habit(data: Data, name: str) -> bool:
    """Delete a habit and its target. Returns False if it does not exist."""
    if name not in data["habits"]:
        return False
    del data["habits"][name]
    data.get("targets", {}).pop(name, None)
    return True


def rename_habit(data: Data, old: str, new: str) -> None:
    """Rename a habit, carrying its history and target over."""
    if old not in data["habits"]:
        raise KeyError(old)
    if new in data["habits"]:
        raise ValueError(f"habit '{new}' already exists")
    data["habits"][new] = data["habits"].pop(old)
    targets = data.setdefault("targets", {})
    if old in targets:
        targets[new] = targets.pop(old)


def monthly_summary(data: Data, year: int, month: int) -> dict[str, int]:
    """Check-ins per habit in the given calendar month."""
    prefix = f"{year:04d}-{month:02d}-"
    return {
        name: sum(1 for d in days if d.startswith(prefix))
        for name, days in data["habits"].items()
    }


def days_in_month(year: int, month: int) -> int:
    nxt = date(year + (month == 12), month % 12 + 1, 1)
    return (nxt - date(year, month, 1)).days


def search_notes(data: Data, query: str) -> list[dict[str, str]]:
    """Notes whose text contains the query (case-insensitive), oldest first."""
    q = query.casefold()
    hits = [n for n in data["notes"] if q in n["text"].casefold()]
    return sorted(hits, key=lambda n: n["date"])
