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
selfdev status --json          # machine-readable (also: weekly --json)
selfdev note "learned argparse subcommands" -t python -t cli
selfdev notes                   # list learning notes
selfdev notes -s argparse       # search notes (case-insensitive)
selfdev notes -t python         # only notes with a tag
selfdev weekly                  # check-ins over the last 7 days
selfdev monthly --month 2026-11 # per-habit monthly completion rate
selfdev target coding 3         # weekly goal; shown in `weekly`
selfdev rename coding dev      # rename a habit (history kept)
selfdev remove dev              # delete a habit
selfdev export -o report.md    # Markdown report (stdout if -o omitted)
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
ruff check .
mypy src
pytest
```

CI runs ruff, mypy (strict) and the tests on Python 3.10 and 3.12.

## Roadmap

- [x] Weekly summary report (`selfdev weekly`)
- [x] Export notes to Markdown (`selfdev export`)
- [x] Per-habit weekly targets (`selfdev target`)
- [x] Remove and rename habits (`selfdev remove`, `selfdev rename`)
- [x] `--json` output for status and weekly
- [x] Monthly report (`selfdev monthly`)
- [x] Type hints and lint (ruff, mypy --strict) in CI
- [x] Search notes (`selfdev notes --search`)
- [x] Tags for notes (`selfdev note -t`, `selfdev notes -t`)
- [ ] CSV import/export
- [ ] Habit archive (hide without deleting)
- [ ] Shell completion

## License

MIT
