"""JSON-file persistence for habits and learning notes."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

Data = dict[str, Any]
"""Shape: {'habits': {name: [iso dates]}, 'notes': [...], 'targets': {name: int}}."""


def default_path() -> Path:
    """Data file location; override with the SELFDEV_DATA environment variable."""
    env = os.environ.get("SELFDEV_DATA")
    return Path(env) if env else Path.home() / ".selfdev" / "data.json"


def load(path: Path) -> Data:
    if not path.exists():
        return {"habits": {}, "notes": [], "targets": {}}
    with path.open(encoding="utf-8") as f:
        data: Data = json.load(f)
    data.setdefault("habits", {})
    data.setdefault("notes", [])
    data.setdefault("targets", {})
    return data


def save(path: Path, data: Data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
    tmp.replace(path)
