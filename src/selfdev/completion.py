"""Shell completion script generation (bash and zsh), derived from the argparse parser."""
from __future__ import annotations

import argparse

HABIT_ARGS = {"habit", "old"}  # positional names that take an existing habit


def _subcommands(parser: argparse.ArgumentParser) -> dict[str, argparse.ArgumentParser]:
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return {n: p for n, p in action.choices.items() if not n.startswith("_")}
    return {}


def _options(sub: argparse.ArgumentParser) -> list[str]:
    opts: list[str] = []
    for action in sub._actions:
        opts += [o for o in action.option_strings if o not in ("-h", "--help")]
    return opts


def _takes_habit(sub: argparse.ArgumentParser) -> bool:
    positionals = [a.dest for a in sub._actions if not a.option_strings]
    return bool(positionals) and positionals[0] in HABIT_ARGS


def generate(parser: argparse.ArgumentParser, shell: str) -> str:
    """Return a completion script. `shell` is 'bash' or 'zsh'."""
    if shell not in ("bash", "zsh"):
        raise ValueError(f"unsupported shell: {shell}")
    subs = _subcommands(parser)
    names = " ".join(sorted(subs))
    option_cases = "\n".join(
        f"      {name}) opts=\"{' '.join(_options(sub))}\";;"
        for name, sub in sorted(subs.items())
        if _options(sub)
    )
    habit_cmds = "|".join(sorted(n for n, s in subs.items() if _takes_habit(s)))
    prelude = "autoload -U +X bashcompinit && bashcompinit\n" if shell == "zsh" else ""
    return f"""{prelude}_selfdev() {{
  local cur cmd opts
  cur="${{COMP_WORDS[COMP_CWORD]}}"
  cmd="${{COMP_WORDS[1]}}"
  if [ "$COMP_CWORD" -eq 1 ]; then
    COMPREPLY=($(compgen -W "{names}" -- "$cur"))
    return
  fi
  if [[ "$cur" == -* ]]; then
    case "$cmd" in
{option_cases}
    esac
    COMPREPLY=($(compgen -W "$opts" -- "$cur"))
    return
  fi
  case "$cmd" in
    {habit_cmds})
      if [ "$COMP_CWORD" -eq 2 ]; then
        COMPREPLY=($(compgen -W "$(selfdev _habits 2>/dev/null)" -- "$cur"))
      fi;;
  esac
}}
complete -F _selfdev selfdev
"""
