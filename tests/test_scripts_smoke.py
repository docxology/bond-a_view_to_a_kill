"""Subprocess smoke tests for the thin ZORIN CLI scripts.

Each script self-bootstraps ``src/`` onto ``sys.path``, so ``python
scripts/x.py`` works from the package root. We drive them with the venv
interpreter and assert exit codes + artifact output — all real I/O, no mocks.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = PROJECT_ROOT / "scripts"


def _run(script: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )


def test_mission_brief_runs() -> None:
    result = _run("mission_brief.py")
    assert result.returncode == 0, result.stderr
    assert "ZORIN" in result.stdout


def test_mission_recon_runs_with_default_goal() -> None:
    result = _run("mission_recon.py")
    assert result.returncode == 0, result.stderr
    assert "Recon report" in result.stdout


def test_mission_recon_runs_with_custom_goal() -> None:
    result = _run("mission_recon.py", "locate the flooding adit")
    assert result.returncode == 0, result.stderr
    assert "locate the flooding adit" in result.stdout


def test_mission_plan_runs() -> None:
    result = _run("mission_plan.py")
    assert result.returncode == 0, result.stderr
    assert "Mission plan steps" in result.stdout
    assert "supply_chain" in result.stdout


def test_mission_execute_runs_and_reports_metrics() -> None:
    result = _run("mission_execute.py")
    assert result.returncode == 0, result.stderr
    assert "success=True" in result.stdout
    assert "[chip]" in result.stdout and "[flood]" in result.stdout and "[race]" in result.stdout


def test_mission_debrief_runs() -> None:
    result = _run("mission_debrief.py")
    assert result.returncode == 0, result.stderr
    assert "Lessons:" in result.stdout


def test_z_generate_writes_artifacts() -> None:
    result = _run("z_generate_manuscript_variables.py")
    assert result.returncode == 0, result.stderr
    data = PROJECT_ROOT / "output" / "data" / "manuscript_variables.json"
    assert data.is_file()
    for figure in ("choke_points.png", "flood_curve.png", "race_cover.png"):
        assert (PROJECT_ROOT / "output" / "figures" / figure).is_file()
