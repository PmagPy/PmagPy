"""Tests for the retired, temporarily registered MagIC 2 commands."""

import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("legacy", ["aniso_magic2", "chi_magic2"])
def test_retired_command_exits_with_migration_message(legacy, tmp_path):
    result = subprocess.run(
        [sys.executable, str(ROOT / "programs" / (legacy + ".py")), "-f", "input.txt"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert legacy + ".py is retired" in result.stderr
    assert not list(tmp_path.iterdir())
