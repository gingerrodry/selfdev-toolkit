from datetime import date

from selfdev import habits


def test_check_in_is_idempotent():
    data = {"habits": {}, "notes": []}
    assert habits.check_in(data, "code", date(2026, 1, 1)) is True
    assert habits.check_in(data, "code", date(2026, 1, 1)) is False
    assert data["habits"]["code"] == ["2026-01-01"]


def test_current_streak_counts_consecutive_days():
    days = ["2026-01-01", "2026-01-02", "2026-01-03"]
    assert habits.current_streak(days, date(2026, 1, 3)) == 3


def test_current_streak_survives_unfinished_today():
    days = ["2026-01-01", "2026-01-02"]
    assert habits.current_streak(days, date(2026, 1, 3)) == 2


def test_current_streak_breaks_after_gap():
    assert habits.current_streak(["2026-01-01"], date(2026, 1, 5)) == 0


def test_longest_streak():
    days = ["2026-01-01", "2026-01-02", "2026-01-05", "2026-01-06", "2026-01-07"]
    assert habits.longest_streak(days) == 3
    assert habits.longest_streak([]) == 0


def test_weekly_summary_counts_last_seven_days_only():
    data = {"habits": {"code": ["2026-01-01", "2026-01-04", "2026-01-10"]}, "notes": []}
    # window is 2026-01-04 .. 2026-01-10
    assert habits.weekly_summary(data, date(2026, 1, 10)) == {"code": 2}


def test_set_target_validates_range():
    import pytest

    data = {"habits": {}, "notes": []}
    habits.set_target(data, "code", 3)
    assert data["targets"] == {"code": 3}
    with pytest.raises(ValueError):
        habits.set_target(data, "code", 0)


def test_remove_habit_drops_target_too():
    data = {"habits": {"a": ["2026-01-01"]}, "notes": [], "targets": {"a": 2}}
    assert habits.remove_habit(data, "a") is True
    assert data["habits"] == {} and data["targets"] == {}
    assert habits.remove_habit(data, "a") is False


def test_rename_habit_keeps_history_and_target():
    import pytest

    data = {"habits": {"a": ["2026-01-01"], "b": []}, "notes": [], "targets": {"a": 2}}
    habits.rename_habit(data, "a", "c")
    assert data["habits"]["c"] == ["2026-01-01"] and data["targets"] == {"c": 2}
    with pytest.raises(ValueError):
        habits.rename_habit(data, "c", "b")
    with pytest.raises(KeyError):
        habits.rename_habit(data, "zzz", "y")


def test_monthly_summary_and_days_in_month():
    data = {"habits": {"a": ["2026-01-31", "2026-02-01", "2026-02-15"]}, "notes": []}
    assert habits.monthly_summary(data, 2026, 2) == {"a": 2}
    assert habits.days_in_month(2026, 2) == 28
    assert habits.days_in_month(2028, 2) == 29
    assert habits.days_in_month(2026, 12) == 31


def test_search_notes_is_case_insensitive_and_sorted():
    data = {
        "habits": {},
        "targets": {},
        "notes": [
            {"date": "2026-01-03", "text": "Learned Argparse"},
            {"date": "2026-01-01", "text": "argparse subcommands"},
            {"date": "2026-01-02", "text": "pytest fixtures"},
        ],
    }
    hits = habits.search_notes(data, "ARGPARSE")
    assert [n["date"] for n in hits] == ["2026-01-01", "2026-01-03"]
    assert habits.search_notes(data, "zzz") == []


def test_normalize_tags():
    assert habits.normalize_tags([" #Python", "python", "", "CLI"]) == ["python", "cli"]


def test_filter_by_tag_handles_legacy_notes():
    notes = [
        {"date": "2026-01-01", "text": "a"},
        {"date": "2026-01-02", "text": "b", "tags": ["x"]},
    ]
    assert habits.filter_by_tag(notes, "#X") == [notes[1]]
    assert habits.filter_by_tag(notes, "  ") == []
