"""Habit tracking logic: check-ins and streak calculation."""
from __future__ import annotations

from collections.abc import Iterable
from datetime import date, timedelta
from typing import Any

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


MAX_FREEZES_PER_MONTH = 2


def _dates(days: Iterable[str]) -> set[date]:
    return {date.fromisoformat(d) for d in days}


def current_streak(days: list[str], today: date, frozen: Iterable[str] = ()) -> int:
    """Consecutive days ending today (or yesterday, so an unfinished day keeps the streak).

    A frozen day keeps the streak alive but does not add to it.
    """
    done, skipped = _dates(days), _dates(frozen)
    cursor = today if today in done else today - timedelta(days=1)
    streak = 0
    while cursor in done or cursor in skipped:
        if cursor in done:
            streak += 1
        cursor -= timedelta(days=1)
    return streak


def longest_streak(days: list[str], frozen: Iterable[str] = ()) -> int:
    """Longest run of check-ins; gaps made up only of frozen days do not break a run."""
    skipped = _dates(frozen)
    best = run = 0
    prev: date | None = None
    for d in sorted(_dates(days)):
        gap = [prev + timedelta(days=k) for k in range(1, (d - prev).days)] if prev else []
        bridged = prev is not None and all(g in skipped for g in gap)
        run = run + 1 if bridged else 1
        best = max(best, run)
        prev = d
    return best


def freeze(data: Data, name: str, day: date, today: date) -> None:
    """Freeze `day` for a habit so a missed day does not break its streak.

    Raises KeyError (unknown habit) or ValueError (future day, already checked in,
    already frozen, or the monthly limit is used up).
    """
    if name not in data["habits"]:
        raise KeyError(name)
    if day > today:
        raise ValueError("cannot freeze a future day")
    iso = day.isoformat()
    if iso in data["habits"][name]:
        raise ValueError(f"{iso} already has a check-in")
    frozen: list[str] = data.setdefault("freezes", {}).setdefault(name, [])
    if iso in frozen:
        raise ValueError(f"{iso} is already frozen")
    month = iso[:7]
    if sum(1 for f in frozen if f.startswith(month)) >= MAX_FREEZES_PER_MONTH:
        raise ValueError(f"at most {MAX_FREEZES_PER_MONTH} freezes per habit per month ({month})")
    frozen.append(iso)
    frozen.sort()


def due_today(data: Data, today: date) -> list[tuple[str, int]]:
    """Active habits with no check-in (and no freeze) today, as (name, current streak).

    The streak shown is the one still alive, i.e. what a missed day would end.
    """
    due: list[tuple[str, int]] = []
    for name, days in sorted(active_habits(data).items()):
        iso = today.isoformat()
        if iso in days or iso in frozen_days(data, name):
            continue
        due.append((name, current_streak(days, today, frozen_days(data, name))))
    return due


def frozen_days(data: Data, name: str) -> list[str]:
    result: list[str] = data.get("freezes", {}).get(name, [])
    return result


def uncheck(data: Data, name: str, day: date) -> bool:
    """Undo a check-in. Returns False if that day was not recorded.

    The habit itself is kept even when its last check-in is removed.
    """
    days = data["habits"].get(name)
    iso = day.isoformat()
    if days is None or iso not in days:
        return False
    days.remove(iso)
    return True


def active_habits(data: Data) -> dict[str, list[str]]:
    """Habits that are not archived."""
    archived = set(data.get("archived", []))
    return {n: d for n, d in data["habits"].items() if n not in archived}


def archive_habit(data: Data, name: str) -> bool:
    """Hide a habit from reports while keeping its history. False if already archived."""
    if name not in data["habits"]:
        raise KeyError(name)
    archived: list[str] = data.setdefault("archived", [])
    if name in archived:
        return False
    archived.append(name)
    return True


def unarchive_habit(data: Data, name: str) -> bool:
    """Bring an archived habit back. False if it was not archived."""
    archived: list[str] = data.setdefault("archived", [])
    if name not in archived:
        return False
    archived.remove(name)
    return True


def weekly_summary(data: Data, today: date) -> dict[str, int]:
    """Check-ins per habit over the 7 days ending today (inclusive)."""
    start = today - timedelta(days=6)
    result = {}
    for name, days in active_habits(data).items():
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
    data.get("freezes", {}).pop(name, None)
    if name in data.get("archived", []):
        data["archived"].remove(name)
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
    archived: list[str] = data.setdefault("archived", [])
    if old in archived:
        archived[archived.index(old)] = new
    freezes = data.setdefault("freezes", {})
    if old in freezes:
        freezes[new] = freezes.pop(old)


def monthly_summary(data: Data, year: int, month: int) -> dict[str, int]:
    """Check-ins per habit in the given calendar month."""
    prefix = f"{year:04d}-{month:02d}-"
    return {
        name: sum(1 for d in days if d.startswith(prefix))
        for name, days in active_habits(data).items()
    }


def days_in_month(year: int, month: int) -> int:
    nxt = date(year + (month == 12), month % 12 + 1, 1)
    return (nxt - date(year, month, 1)).days


def search_notes(data: Data, query: str) -> list[dict[str, Any]]:
    """Notes whose text contains the query (case-insensitive), oldest first."""
    q = query.casefold()
    hits = [n for n in data["notes"] if q in n["text"].casefold()]
    return sorted(hits, key=lambda n: n["date"])


def edit_note(data: Data, number: int, text: str) -> None:
    """Replace the text of note `number` (1-based, position in the full list)."""
    if not 1 <= number <= len(data["notes"]):
        raise IndexError(number)
    if not text.strip():
        raise ValueError("note text must not be empty")
    data["notes"][number - 1]["text"] = text


def delete_note(data: Data, number: int) -> dict[str, Any]:
    """Remove and return note `number` (1-based, position in the full list)."""
    if not 1 <= number <= len(data["notes"]):
        raise IndexError(number)
    removed: dict[str, Any] = data["notes"].pop(number - 1)
    return removed


def normalize_tags(tags: list[str]) -> list[str]:
    """Lowercase, strip a leading '#', drop empties and duplicates (order kept)."""
    seen: list[str] = []
    for t in tags:
        t = t.strip().lstrip("#").casefold()
        if t and t not in seen:
            seen.append(t)
    return seen


def filter_by_tag(notes: list[dict[str, Any]], tag: str) -> list[dict[str, Any]]:
    """Notes carrying the tag. Notes saved before tags existed have none."""
    wanted = normalize_tags([tag])
    if not wanted:
        return []
    return [n for n in notes if wanted[0] in n.get("tags", [])]
