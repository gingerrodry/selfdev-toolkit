import shutil
import subprocess
from datetime import date

import pytest

from selfdev import completion
from selfdev.cli import build_parser, main

DAY = date(2026, 1, 10)


def test_generate_lists_public_commands_only():
    script = completion.generate(build_parser(), "bash")
    assert "archive check completion export" in script
    assert "_habits" not in script.split("compgen -W")[1]  # hidden command not offered
    assert "status) opts=\"--json --all\"" in script
    assert "archive|check|remove|rename|target|unarchive)" in script


def test_script_strips_backslashes_not_slashes():
    script = completion.generate(build_parser(), "bash")
    assert 'cur="${cur//\\\\/}"' in script
    assert "local IFS=$'\\n'" in script


def test_zsh_prelude_and_unknown_shell():
    assert completion.generate(build_parser(), "zsh").startswith("autoload -U +X bashcompinit")
    assert not completion.generate(build_parser(), "bash").startswith("autoload")
    with pytest.raises(ValueError, match="fish"):
        completion.generate(build_parser(), "fish")


def test_cli_completion_and_hidden_habits(tmp_path, capsys):
    d = str(tmp_path / "d.json")
    assert main(["completion", "bash"], today=DAY) == 0
    assert "complete -F _selfdev selfdev" in capsys.readouterr().out
    main(["--data", d, "check", "zeta"], today=DAY)
    main(["--data", d, "check", "alpha"], today=DAY)
    capsys.readouterr()
    main(["--data", d, "_habits"], today=DAY)
    assert capsys.readouterr().out == "alpha\nzeta\n"


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash not available")
def test_generated_script_completes_in_real_bash(tmp_path):
    script = tmp_path / "comp.sh"
    script.write_text(completion.generate(build_parser(), "bash"), encoding="utf-8")
    # stub `selfdev` so the script's habit lookup does not need an installed entry point
    stub = tmp_path / "selfdev"
    habits = "alpha\\nbeta\\ndeep work\\nread/write\\n"
    stub.write_text(f"#!/bin/sh\nprintf '{habits}'\n", encoding="utf-8")
    stub.chmod(0o755)

    def complete(words: list[str], index: int) -> list[str]:
        arr = " ".join(f"'{w}'" for w in words)
        cmd = (
            f"export PATH={tmp_path}:$PATH; source {script}; "
            f"COMP_WORDS=({arr}); COMP_CWORD={index}; _selfdev; "
            'printf "%s\\n" "${COMPREPLY[@]}"'
        )
        out = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True, check=True)
        return [line for line in out.stdout.splitlines() if line]

    assert complete(["selfdev", "wee"], 1) == ["weekly"]
    assert complete(["selfdev", "status", "--j"], 2) == ["--json"]
    assert complete(["selfdev", "check", "a"], 2) == ["alpha"]
    assert complete(["selfdev", "rename", "b"], 2) == ["beta"]
    assert complete(["selfdev", "note", ""], 2) == []
    # names with spaces are offered shell-escaped, and an escaped prefix still matches
    assert complete(["selfdev", "check", "de"], 2) == ["deep\\ work"]
    assert complete(["selfdev", "check", "deep\\ w"], 2) == ["deep\\ work"]
    assert complete(["selfdev", "archive", ""], 2) == [
        "alpha",
        "beta",
        "deep\\ work",
        "read/write",
    ]
    # a slash in the typed prefix must be kept (only backslashes are stripped)
    assert complete(["selfdev", "check", "read/"], 2) == ["read/write"]
    assert complete(["selfdev", "check", "/"], 2) == []
