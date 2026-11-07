from selfdev import store


def test_load_missing_file_returns_empty(tmp_path):
    assert store.load(tmp_path / "none.json") == {"habits": {}, "notes": [], "targets": {}}


def test_roundtrip(tmp_path):
    p = tmp_path / "sub" / "data.json"
    data = {"habits": {"日本語": ["2026-01-01"]}, "notes": [], "targets": {"日本語": 3}}
    store.save(p, data)
    assert store.load(p) == data


def test_load_old_file_without_targets(tmp_path):
    p = tmp_path / "old.json"
    p.write_text('{"habits": {}, "notes": []}', encoding="utf-8")
    assert store.load(p)["targets"] == {}
