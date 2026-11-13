"""Command-line interface for selfdev."""
from __future__ import annotations

import argparse
import json
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

    st = sub.add_parser("status", help="show streaks for all habits")
    st.add_argument("--json", action="store_true", help="machine-readable output")
    t = sub.add_parser("target", help="set a weekly goal for a habit (1-7)")
    t.add_argument("habit")
    t.add_argument("per_week", type=int)
    r = sub.add_parser("remove", help="delete a habit and its history")
    r.add_argument("habit")
    m = sub.add_parser("rename", help="rename a habit, keeping its history")
    m.add_argument("old")
    m.add_argument("new")
    mo = sub.add_parser("monthly", help="show check-ins for a calendar month")
    mo.add_argument("--month", help="YYYY-MM (default: current month)")
    wk = sub.add_parser("weekly", help="show check-ins for the last 7 days")
    wk.add_argument("--json", action="store_true", help="machine-readable output")

    n = sub.add_parser("note", help="add a learning note")
    n.add_argument("text")
    n.add_argument("-t", "--tag", action="append", default=[], help="tag (repeatable)")

    ns = sub.add_parser("notes", help="list learning notes")
    ns.add_argument("-s", "--search", help="only notes containing this text (case-insensitive)")
    ns.add_argument("-t", "--tag", help="only notes with this tag")

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
    elif args.cmd == "status" and args.json:
        out = {
            name: {
                "current": habits.current_streak(days, today),
                "best": habits.longest_streak(days),
                "total": len(days),
            }
            for name, days in sorted(data["habits"].items())
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
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
    elif args.cmd == "remove":
        if not habits.remove_habit(data, args.habit):
            print(f"error: no such habit '{args.habit}'", file=sys.stderr)
            return 2
        store.save(path, data)
        print(f"Removed '{args.habit}'.")
    elif args.cmd == "rename":
        try:
            habits.rename_habit(data, args.old, args.new)
        except KeyError:
            print(f"error: no such habit '{args.old}'", file=sys.stderr)
            return 2
        except ValueError as err:
            print(f"error: {err}", file=sys.stderr)
            return 2
        store.save(path, data)
        print(f"Renamed '{args.old}' -> '{args.new}'.")
    elif args.cmd == "monthly":
        try:
            year, month = (
                map(int, args.month.split("-")) if args.month else (today.year, today.month)
            )
            total = habits.days_in_month(year, month)
        except (ValueError, TypeError):
            print("error: --month must look like 2026-11", file=sys.stderr)
            return 2
        summary = habits.monthly_summary(data, year, month)
        print(f"Report for {year:04d}-{month:02d} ({total} days)")
        if not summary:
            print("No habits yet. Try: selfdev check coding")
        for name, count in sorted(summary.items()):
            pct = round(100 * count / total)
            print(f"{name}: {count}/{total} ({pct}%)")
        notes = [n for n in data["notes"] if n["date"].startswith(f"{year:04d}-{month:02d}-")]
        print(f"Notes: {len(notes)}")
    elif args.cmd == "weekly" and args.json:
        summary = habits.weekly_summary(data, today)
        out = {
            name: {"count": count, "goal": data["targets"].get(name)}
            for name, count in sorted(summary.items())
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
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
        note = {"date": today.isoformat(), "text": args.text}
        tags = habits.normalize_tags(args.tag)
        if tags:
            note["tags"] = tags
        data["notes"].append(note)
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
        shown = habits.search_notes(data, args.search) if args.search else data["notes"]
        if args.tag:
            shown = habits.filter_by_tag(shown, args.tag)
        if (args.search or args.tag) and not shown:
            print("No matching notes.")
        for item in shown:
            suffix = "".join(f" #{t}" for t in item.get("tags", []))
            print(f"{item['date']}  {item['text']}{suffix}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
