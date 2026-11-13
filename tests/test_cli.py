from datetime import date

from selfdev.cli import main

DAY = date(2026, 1, 10)


def run(tmp_path, *argv, today=DAY):
    return main(["--data", str(tmp_path / "d.json"), *argv], today=today)


def test_check_then_status(tmp_path, capsys):
    run(tmp_path, "check", "coding")
    run(tmp_path, "check", "coding", today=date(2026, 1, 11))
    capsys.readouterr()
    run(tmp_path, "status", today=date(2026, 1, 11))
    assert "coding: current 2 / best 2 / total 2" in capsys.readouterr().out


def test_duplicate_check_in(tmp_path, capsys):
    run(tmp_path, "check", "coding")
    run(tmp_path, "check", "coding")
    assert "already checked in" in capsys.readouterr().out


def test_notes(tmp_path, capsys):
    run(tmp_path, "note", "learned argparse subcommands")
    capsys.readouterr()
    run(tmp_path, "notes")
    assert "2026-01-10  learned argparse subcommands" in capsys.readouterr().out


def test_weekly_report(tmp_path, capsys):
    run(tmp_path, "check", "coding", today=date(2026, 1, 9))
    run(tmp_path, "check", "coding")
    run(tmp_path, "note", "weekly test")
    capsys.readouterr()
    run(tmp_path, "weekly")
    out = capsys.readouterr().out
    assert "coding: ##..... 2/7" in out
    assert "Notes this week: 1" in out


def test_target_shown_in_weekly(tmp_path, capsys):
    run(tmp_path, "check", "coding")
    run(tmp_path, "target", "coding", "1")
    capsys.readouterr()
    run(tmp_path, "weekly")
    assert "(goal 1: met)" in capsys.readouterr().out
    run(tmp_path, "target", "coding", "3")
    capsys.readouterr()
    run(tmp_path, "weekly")
    assert "(goal 3: not yet)" in capsys.readouterr().out


def test_target_rejects_out_of_range(tmp_path, capsys):
    assert run(tmp_path, "target", "coding", "9") == 2
    assert "between 1 and 7" in capsys.readouterr().err


def test_rename_and_remove_via_cli(tmp_path, capsys):
    run(tmp_path, "check", "old")
    assert run(tmp_path, "rename", "old", "new") == 0
    assert run(tmp_path, "rename", "old", "x") == 2
    capsys.readouterr()
    run(tmp_path, "status")
    assert "new: current 1" in capsys.readouterr().out
    assert run(tmp_path, "remove", "new") == 0
    assert run(tmp_path, "remove", "new") == 2


def test_status_json(tmp_path, capsys):
    import json

    run(tmp_path, "check", "日本語")
    capsys.readouterr()
    run(tmp_path, "status", "--json")
    assert json.loads(capsys.readouterr().out) == {
        "日本語": {"current": 1, "best": 1, "total": 1}
    }


def test_weekly_json_includes_goal(tmp_path, capsys):
    import json

    run(tmp_path, "check", "code")
    run(tmp_path, "target", "code", "3")
    capsys.readouterr()
    run(tmp_path, "weekly", "--json")
    assert json.loads(capsys.readouterr().out) == {"code": {"count": 1, "goal": 3}}


def test_monthly_report(tmp_path, capsys):
    run(tmp_path, "check", "code", today=date(2026, 1, 3))
    run(tmp_path, "check", "code", today=date(2026, 1, 4))
    capsys.readouterr()
    run(tmp_path, "monthly")
    out = capsys.readouterr().out
    assert "Report for 2026-01 (31 days)" in out
    assert "code: 2/31 (6%)" in out
    run(tmp_path, "monthly", "--month", "2025-12")
    assert "code: 0/31 (0%)" in capsys.readouterr().out


def test_monthly_rejects_bad_month(tmp_path, capsys):
    assert run(tmp_path, "monthly", "--month", "nope") == 2
    assert run(tmp_path, "monthly", "--month", "2026-13") == 2
    assert "2026-11" in capsys.readouterr().err


def test_notes_search(tmp_path, capsys):
    run(tmp_path, "note", "learned argparse")
    run(tmp_path, "note", "pytest fixtures")
    capsys.readouterr()
    run(tmp_path, "notes", "--search", "PYTEST")
    out = capsys.readouterr().out
    assert "pytest fixtures" in out and "argparse" not in out
    run(tmp_path, "notes", "-s", "nothing")
    assert "No matching notes." in capsys.readouterr().out


def test_note_tags_and_filter(tmp_path, capsys):
    run(tmp_path, "note", "learned argparse", "-t", "Python", "--tag", "#cli", "-t", "python")
    run(tmp_path, "note", "old untagged note")
    capsys.readouterr()
    run(tmp_path, "notes")
    out = capsys.readouterr().out
    assert "learned argparse #python #cli" in out
    assert "old untagged note\n" in out
    run(tmp_path, "notes", "--tag", "CLI")
    out = capsys.readouterr().out
    assert "learned argparse" in out and "untagged" not in out
    run(tmp_path, "notes", "-t", "missing")
    assert "No matching notes." in capsys.readouterr().out
