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
