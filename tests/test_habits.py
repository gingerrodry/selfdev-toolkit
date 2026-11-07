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
