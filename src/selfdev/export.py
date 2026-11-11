"""Export notes and habit stats as Markdown."""
from __future__ import annotations

from datetime import date

from . import habits
from .store import Data


def to_markdown(data: Data, today: date) -> str:
    lines = [f"# selfdev report ({today.isoformat()})", "", "## Habits", ""]
    if data["habits"]:
        lines += ["| Habit | Current | Best | Total |", "|---|---|---|---|"]
        for name, days in sorted(data["habits"].items()):
            lines.append(
                f"| {name} | {habits.current_streak(days, today)} "
                f"| {habits.longest_streak(days)} | {len(days)} |"
            )
    else:
        lines.append("_No habits yet._")
    lines += ["", "## Notes", ""]
    if data["notes"]:
        for n in sorted(data["notes"], key=lambda n: n["date"]):
            lines.append(f"- **{n['date']}** {n['text']}")
    else:
        lines.append("_No notes yet._")
    return "\n".join(lines) + "\n"
