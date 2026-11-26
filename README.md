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
selfdev due                     # habits not yet checked in today, with streaks at risk (--json too)
selfdev freeze coding           # protect a missed day (--date YYYY-MM-DD; max 2 per habit per month)
selfdev unfreeze coding         # undo a freeze (gives the monthly slot back)
selfdev uncheck coding          # undo today's check-in (--date YYYY-MM-DD for another day)
selfdev status                  # current / best streak and totals
selfdev status --json          # machine-readable (also: weekly --json)
selfdev note "learned argparse subcommands" -t python -t cli
selfdev notes                   # list learning notes
selfdev notes -s argparse       # search notes (case-insensitive)
selfdev notes -t python         # only notes with a tag
selfdev notes -n                # show note numbers
selfdev note-edit 2 "new text"  # change a note (date and tags are kept)
selfdev note-rm 2               # delete a note (numbers are positions in the full list)
selfdev weekly                  # check-ins over the last 7 days
selfdev monthly --month 2026-11 # per-habit monthly completion rate
selfdev target coding 3         # weekly goal; shown in `weekly`
selfdev rename coding dev      # rename a habit (history kept)
selfdev remove dev              # delete a habit
selfdev archive dev             # hide from reports, keep history (status --all shows it)
selfdev unarchive dev           # bring it back
selfdev export -o report.md    # Markdown report (stdout if -o omitted)
selfdev export -f csv -o c.csv # check-ins as CSV (habit,date)
selfdev import c.csv           # merge check-ins from CSV; existing ones are skipped
```

### Shell completion

```bash
echo 'eval "$(selfdev completion bash)"' >> ~/.bashrc   # bash
echo 'eval "$(selfdev completion zsh)"' >> ~/.zshrc     # zsh
selfdev completion fish > ~/.config/fish/completions/selfdev.fish   # fish
```

Completes subcommands, options, and existing habit names (names with spaces are shell-escaped). Limitation (bash/zsh): a global `--data` before the subcommand shifts the word positions, so complete without it. The bash script is tested in real bash and the fish script in real fish; zsh relies on its bash-compatibility layer and is not tested.

Data lives in `~/.selfdev/data.json`. Override with `--data PATH` or the `SELFDEV_DATA` environment variable.

## Design

- `store.py`: JSON load/save with atomic writes (temp file + replace)
- `habits.py`: pure functions for check-ins and streaks; today's date is injected, so logic is deterministic to test
- `cli.py`: thin argparse layer over the above

A streak stays alive if you haven't checked in yet today but did yesterday. A frozen day keeps a streak alive but does not add to it (and is not counted in the total); each habit can freeze at most 2 days per month, and only past or current days without a check-in.

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
- [x] CSV import/export (`selfdev export -f csv`, `selfdev import`)
- [x] Habit archive (`selfdev archive`, `selfdev unarchive`)
- [x] Shell completion (`selfdev completion bash|zsh|fish`)
- [x] Fish completion (`selfdev completion fish`)
- [x] Undo a check-in (`selfdev uncheck`)
- [x] Edit or delete a note (`selfdev note-edit`, `selfdev note-rm`)
- [x] Streak freeze (`selfdev freeze`)
- [ ] Show frozen days in `status --json` and the Markdown export
- [x] `selfdev unfreeze` to undo a freeze
- [x] List habits not yet checked in today (`selfdev due`)
- [ ] Unit tests for the data-migration path of old data files
- [x] Habit-name completion for names containing spaces or slashes

## License

MIT
