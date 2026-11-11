"""Tests for the retired, temporarily registered MagIC 2 commands."""

import subprocess
import sys
from pathlib import Path

import pytest

from programs_list import programs_list


ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    "legacy,replacement",
    [("aniso_magic2", "aniso_magic"), ("chi_magic2", "chi_magic")],
)
@pytest.mark.parametrize("args", [[], ["-f", "input.txt"], ["-h"]])
def test_retired_commands(legacy, replacement, args, tmp_path):
    result = subprocess.run(
        [sys.executable, str(ROOT / "programs" / (legacy + ".py")), *args],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == (0 if args == ["-h"] else 1)
    message = result.stdout if args == ["-h"] else result.stderr
    assert legacy + ".py is retired" in message
    assert "Convert MagIC Data Model 2 files to Data Model 3" in message
    assert "use " + replacement + ".py" in message
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("legacy", ["aniso_magic2", "chi_magic2"])
def test_retired_command_remains_registered(legacy):
    assert f"{legacy}.py=programs.{legacy}:main" in programs_list
