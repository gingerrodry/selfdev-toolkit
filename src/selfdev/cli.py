"""Command-line interface for selfdev."""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from . import __version__, habits, store
from .export import to_markdown


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="selfdev", description="Habit streaks and learning log")
    p.add_argument("--version", action="version", version=__version__)
    p.add_argument("--data", type=Path, help="data file (default: ~/.selfdev/data.json)")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("check", help="check in a habit for today")
    c.add_argument("habit")

    sub.add_parser("status", help="show streaks for all habits")
    t = sub.add_parser("target", help="set a weekly goal for a habit (1-7)")
    t.add_argument("habit")
    t.add_argument("per_week", type=int)
    sub.add_parser("weekly", help="show check-ins for the last 7 days")

    n = sub.add_parser("note", help="add a learning note")
    n.add_argument("text")

    sub.add_parser("notes", help="list learning notes")

    e = sub.add_parser("export", help="export habits and notes as Markdown")
    e.add_argument("-o", "--output", type=Path, help="write to file instead of stdout")
    return p


def main(argv: list[str] | None = None, today: date | None = None) -> int:
    args = build_parser().parse_args(argv)
    path = args.data or store.default_path()
    today = today or date.today()
    data = store.load(path)

    if args.cmd == "check":
        if habits.check_in(data, args.habit, today):
            store.save(path, data)
            streak = habits.current_streak(data["habits"][args.habit], today)
            print(f"Checked in '{args.habit}'. Streak: {streak} day(s)")
        else:
            print(f"'{args.habit}' is already checked in today.")
    elif args.cmd == "status":
        if not data["habits"]:
            print("No habits yet. Try: selfdev check coding")
        for name, days in sorted(data["habits"].items()):
            cur = habits.current_streak(days, today)
            best = habits.longest_streak(days)
            print(f"{name}: current {cur} / best {best} / total {len(days)}")
    elif args.cmd == "target":
        try:
            habits.set_target(data, args.habit, args.per_week)
        except ValueError as err:
            print(f"error: {err}", file=sys.stderr)
            return 2
        store.save(path, data)
        print(f"Target for '{args.habit}': {args.per_week}/week")
    elif args.cmd == "weekly":
        summary = habits.weekly_summary(data, today)
        if not summary:
            print("No habits yet. Try: selfdev check coding")
        for name, count in sorted(summary.items()):
            goal = data["targets"].get(name)
            suffix = ""
            if goal:
                suffix = f" (goal {goal}: {'met' if count >= goal else 'not yet'})"
            print(f"{name}: {'#' * count}{'.' * (7 - count)} {count}/7{suffix}")
        notes = [n for n in data["notes"] if (today - date.fromisoformat(n["date"])).days < 7]
        print(f"Notes this week: {len(notes)}")
    elif args.cmd == "note":
        data["notes"].append({"date": today.isoformat(), "text": args.text})
        store.save(path, data)
        print("Note saved.")
    elif args.cmd == "export":
        md = to_markdown(data, today)
        if args.output:
            args.output.write_text(md, encoding="utf-8")
            print(f"Exported to {args.output}")
        else:
            print(md, end="")
    elif args.cmd == "notes":
        for item in data["notes"]:
            print(f"{item['date']}  {item['text']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
