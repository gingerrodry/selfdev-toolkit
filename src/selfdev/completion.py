"""Shell completion script generation (bash and zsh), derived from the argparse parser."""
from __future__ import annotations

import argparse
from pathlib import Path

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


def _fish_quote(text: str) -> str:
    return "'" + text.replace("\\", "\\\\").replace("'", "\\'") + "'"


def _subcommand_help(parser: argparse.ArgumentParser) -> dict[str, str]:
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return {a.dest: a.help or a.dest for a in action._get_subactions()}
    return {}


def _generate_fish(
    parser: argparse.ArgumentParser, subs: dict[str, argparse.ArgumentParser]
) -> str:
    helps = _subcommand_help(parser)
    lines = ["complete -c selfdev -f"]
    for name in sorted(subs):
        lines.append(
            f"complete -c selfdev -n __fish_use_subcommand -a {name} -d {_fish_quote(helps[name])}"
        )
    for name, sub in sorted(subs.items()):
        cond = f"-n '__fish_seen_subcommand_from {name}'"
        for action in sub._actions:
            if action.option_strings:
                if "-h" in action.option_strings:
                    continue
                flags = " ".join(
                    f"-l {o[2:]}" if o.startswith("--") else f"-s {o[1:]}"
                    for o in action.option_strings
                )
                # -r: value is a path, so files may be offered; -x: value is not a file
                if action.nargs == 0:
                    needs_value = ""
                else:
                    needs_value = " -r" if action.type is Path else " -x"
                values = f" -a '{' '.join(action.choices)}'" if action.choices else ""
                desc = f" -d {_fish_quote(action.help)}" if action.help else ""
                lines.append(f"complete -c selfdev {cond} {flags}{needs_value}{values}{desc}")
            elif action.choices:
                lines.append(f"complete -c selfdev {cond} -a '{' '.join(action.choices)}'")
    habit_cmds = " ".join(sorted(n for n, s in subs.items() if _takes_habit(s)))
    lines.append(
        f"complete -c selfdev -n '__fish_seen_subcommand_from {habit_cmds}'"
        " -a '(selfdev _habits 2>/dev/null)'"
    )
    return "\n".join(lines) + "\n"


def generate(parser: argparse.ArgumentParser, shell: str) -> str:
    """Return a completion script. `shell` is 'bash', 'zsh' or 'fish'."""
    if shell not in ("bash", "zsh", "fish"):
        raise ValueError(f"unsupported shell: {shell}")
    subs = _subcommands(parser)
    if shell == "fish":
        return _generate_fish(parser, subs)
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
        local IFS=$'\\n' i
        cur="${{cur//\\\\/}}"
        COMPREPLY=($(compgen -W "$(selfdev _habits 2>/dev/null)" -- "$cur"))
        for i in "${{!COMPREPLY[@]}}"; do
          COMPREPLY[$i]=$(printf '%q' "${{COMPREPLY[$i]}}")
        done
      fi;;
  esac
}}
complete -F _selfdev selfdev
"""
