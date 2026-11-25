from datetime import date

import pytest

from selfdev import habits
from selfdev.cli import main


def make(days, frozen=None):
    return {
        "habits": {"a": list(days)},
        "notes": [],
        "targets": {},
        "archived": [],
        "freezes": {"a": list(frozen)} if frozen else {},
    }


def test_frozen_day_bridges_a_gap_without_counting():
    days = ["2026-01-01", "2026-01-03"]  # 01-02 missed
    assert habits.current_streak(days, date(2026, 1, 3)) == 1  # broken without freeze
    assert habits.current_streak(days, date(2026, 1, 3), ["2026-01-02"]) == 2
    assert habits.longest_streak(days) == 1
    assert habits.longest_streak(days, ["2026-01-02"]) == 2


def test_gap_must_be_fully_frozen():
    days = ["2026-01-01", "2026-01-04"]  # two missed days
    assert habits.longest_streak(days, ["2026-01-02"]) == 1  # only one frozen
    assert habits.longest_streak(days, ["2026-01-02", "2026-01-03"]) == 2


def test_freeze_covers_today_and_yesterday_but_not_beyond():
    days = ["2026-01-01"]
    assert habits.current_streak(days, date(2026, 1, 2), ["2026-01-02"]) == 1
    assert habits.current_streak(days, date(2026, 1, 3), ["2026-01-02"]) == 1
    assert habits.current_streak(days, date(2026, 1, 4), ["2026-01-02"]) == 0


def test_frozen_days_alone_never_make_a_streak():
    assert habits.current_streak([], date(2026, 1, 3), ["2026-01-02", "2026-01-03"]) == 0
    assert habits.longest_streak([], ["2026-01-02"]) == 0


def test_freeze_validation():
    data = make(["2026-01-05"])
    today = date(2026, 1, 10)
    with pytest.raises(KeyError):
        habits.freeze(data, "nope", today, today)
    with pytest.raises(ValueError, match="future"):
        habits.freeze(data, "a", date(2026, 1, 11), today)
    with pytest.raises(ValueError, match="already has a check-in"):
        habits.freeze(data, "a", date(2026, 1, 5), today)
    habits.freeze(data, "a", date(2026, 1, 6), today)
    with pytest.raises(ValueError, match="already frozen"):
        habits.freeze(data, "a", date(2026, 1, 6), today)


def test_monthly_freeze_limit_is_per_month():
    data = make([])
    today = date(2026, 2, 10)
    habits.freeze(data, "a", date(2026, 1, 3), today)
    habits.freeze(data, "a", date(2026, 1, 4), today)
    with pytest.raises(ValueError, match="at most 2"):
        habits.freeze(data, "a", date(2026, 1, 5), today)
    habits.freeze(data, "a", date(2026, 2, 1), today)  # a new month has its own budget


def test_rename_and_remove_carry_freezes():
    data = make(["2026-01-01"], ["2026-01-02"])
    habits.rename_habit(data, "a", "b")
    assert data["freezes"] == {"b": ["2026-01-02"]}
    habits.remove_habit(data, "b")
    assert data["freezes"] == {}


def run(tmp_path, *argv, today=date(2026, 1, 10)):
    return main(["--data", str(tmp_path / "d.json"), *argv], today=today)


def test_cli_freeze_protects_streak_in_status(tmp_path, capsys):
    run(tmp_path, "check", "code", today=date(2026, 1, 8))
    assert run(tmp_path, "freeze", "code", "--date", "2026-01-09") == 0
    run(tmp_path, "check", "code")  # 01-10
    capsys.readouterr()
    run(tmp_path, "status")
    assert "code: current 2 / best 2 / total 2" in capsys.readouterr().out
    run(tmp_path, "export")
    assert "| code | 2 | 2 | 2 |" in capsys.readouterr().out


def test_cli_freeze_errors(tmp_path, capsys):
    run(tmp_path, "check", "code")
    capsys.readouterr()
    assert run(tmp_path, "freeze", "ghost") == 2
    assert "no such habit" in capsys.readouterr().err
    assert run(tmp_path, "freeze", "code", "--date", "yesterday") == 2
    assert "--date must look like" in capsys.readouterr().err
    assert run(tmp_path, "freeze", "code") == 2  # today already has a check-in
    assert "already has a check-in" in capsys.readouterr().err
    assert run(tmp_path, "freeze", "code", "--date", "2026-02-01") == 2
    assert "future" in capsys.readouterr().err


def _due_data():
    return {
        "habits": {"a": ["2026-01-08", "2026-01-09"], "b": ["2026-01-10"], "c": [], "old": []},
        "notes": [],
        "targets": {},
        "archived": ["old"],
        "freezes": {},
    }


def test_due_today_lists_unchecked_active_habits_with_live_streak():
    data = _due_data()
    assert habits.due_today(data, date(2026, 1, 10)) == [("a", 2), ("c", 0)]


def test_due_today_skips_frozen_and_archived():
    data = _due_data()
    data["freezes"] = {"a": ["2026-01-10"]}
    assert habits.due_today(data, date(2026, 1, 10)) == [("c", 0)]  # a frozen, b done, old archived


def test_cli_due_text_json_and_empty(tmp_path, capsys):
    import json

    assert run(tmp_path, "due") == 0
    assert "No habits yet" in capsys.readouterr().out
    run(tmp_path, "check", "code", today=date(2026, 1, 9))
    run(tmp_path, "check", "read")
    capsys.readouterr()
    run(tmp_path, "due")
    assert capsys.readouterr().out == "code  (streak 1 at risk)\n"
    run(tmp_path, "due", "--json")
    assert json.loads(capsys.readouterr().out) == [{"habit": "code", "streak": 1}]
    run(tmp_path, "check", "code")
    capsys.readouterr()
    run(tmp_path, "due")
    assert capsys.readouterr().out == "All done for today.\n"
