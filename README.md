# selfdev-toolkit

![CI](https://github.com/gingerrodry/selfdev-toolkit/actions/workflows/ci.yml/badge.svg)

Python CLI toolkit for developer self-improvement: track daily habits with streaks and keep a learning log. Zero runtime dependencies, data stored in a single JSON file.

## Install

```bash
pip install -e ".[dev]"
```

## Usage

```bash
selfdev check coding            # check in a habit for today
selfdev status                  # current / best streak and totals
selfdev note "learned argparse subcommands"
selfdev notes                   # list learning notes
selfdev weekly                  # check-ins over the last 7 days
```

Data lives in `~/.selfdev/data.json`. Override with `--data PATH` or the `SELFDEV_DATA` environment variable.

## Design

- `store.py`: JSON load/save with atomic writes (temp file + replace)
- `habits.py`: pure functions for check-ins and streaks; today's date is injected, so logic is deterministic to test
- `cli.py`: thin argparse layer over the above

A streak stays alive if you haven't checked in yet today but did yesterday.

## Development

```bash
pip install -e ".[dev]"
pytest
```

CI runs the tests on Python 3.10 and 3.12.

## Roadmap

- [x] Weekly summary report (`selfdev weekly`)
- [ ] Export notes to Markdown
- [ ] Per-habit targets (e.g. 3x per week)

## License

MIT
