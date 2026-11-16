from datetime import date

import pytest

from selfdev import csvio
from selfdev.cli import main

DAY = date(2026, 1, 10)


def make_data():
    return {
        "habits": {"b": ["2026-01-02", "2026-01-01"], "a": ["2026-01-05"], "old": ["2026-01-03"]},
        "notes": [],
        "targets": {},
        "archived": ["old"],
    }


def test_to_csv_sorted_and_skips_archived():
    assert csvio.to_csv(make_data()) == (
        "habit,date\na,2026-01-05\nb,2026-01-01\nb,2026-01-02\n"
    )


def test_roundtrip_with_commas_and_unicode():
    data = {"habits": {"読書, 30分": ["2026-01-01"]}, "notes": [], "targets": {}, "archived": []}
    rows = csvio.parse_csv(csvio.to_csv(data))
    assert rows == [("読書, 30分", "2026-01-01")]


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("", "header"),
        ("name,when\n", "header"),
        ("habit,date\ncode\n", "line 2"),
        ("habit,date\ncode,2026-13-01\n", "invalid date"),
        ("habit,date\n,2026-01-01\n", "line 2"),
    ],
)
def test_parse_rejects_bad_input(text, message):
    with pytest.raises(ValueError, match=message):
        csvio.parse_csv(text)


def test_import_rows_skips_duplicates():
    data = {"habits": {}, "notes": [], "targets": {}, "archived": []}
    rows = [("a", "2026-01-01"), ("a", "2026-01-01"), ("a", "2026-01-02")]
    assert csvio.import_rows(data, rows) == 2
    assert data["habits"]["a"] == ["2026-01-01", "2026-01-02"]


def test_cli_export_import_roundtrip(tmp_path, capsys):
    src, dst, out = tmp_path / "s.json", tmp_path / "d.json", tmp_path / "x.csv"
    main(["--data", str(src), "check", "code"], today=DAY)
    main(["--data", str(src), "export", "-f", "csv", "-o", str(out)], today=DAY)
    capsys.readouterr()
    assert main(["--data", str(dst), "import", str(out)], today=DAY) == 0
    assert "Imported 1 new check-in(s), skipped 0 existing." in capsys.readouterr().out
    main(["--data", str(dst), "import", str(out)], today=DAY)
    assert "Imported 0 new check-in(s), skipped 1 existing." in capsys.readouterr().out


def test_cli_import_errors_do_not_modify_data(tmp_path, capsys):
    bad = tmp_path / "bad.csv"
    bad.write_text("habit,date\ncode,not-a-date\n", encoding="utf-8")
    d = tmp_path / "d.json"
    assert main(["--data", str(d), "import", str(bad)], today=DAY) == 2
    assert "invalid date" in capsys.readouterr().err
    assert not d.exists()
    assert main(["--data", str(d), "import", str(tmp_path / "missing.csv")], today=DAY) == 2
