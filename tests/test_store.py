from selfdev import store


def test_load_missing_file_returns_empty(tmp_path):
    assert store.load(tmp_path / "none.json") == {"habits": {}, "notes": []}


def test_roundtrip(tmp_path):
    p = tmp_path / "sub" / "data.json"
    data = {"habits": {"日本語": ["2026-01-01"]}, "notes": []}
    store.save(p, data)
    assert store.load(p) == data
