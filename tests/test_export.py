from datetime import date

from selfdev.cli import main
from selfdev.export import to_markdown

DAY = date(2026, 1, 10)


def test_empty_report():
    md = to_markdown({"habits": {}, "notes": []}, DAY)
    assert "_No habits yet._" in md and "_No notes yet._" in md


def test_report_contents():
    data = {
        "habits": {"code": ["2026-01-09", "2026-01-10"]},
        "notes": [{"date": "2026-01-10", "text": "hello"}],
    }
    md = to_markdown(data, DAY)
    assert "| code | 2 | 2 | 2 |" in md
    assert "- **2026-01-10** hello" in md


def test_export_to_file(tmp_path, capsys):
    d, out = tmp_path / "d.json", tmp_path / "r.md"
    main(["--data", str(d), "check", "code"], today=DAY)
    main(["--data", str(d), "export", "-o", str(out)], today=DAY)
    assert "| code | 1 | 1 | 1 |" in out.read_text(encoding="utf-8")
