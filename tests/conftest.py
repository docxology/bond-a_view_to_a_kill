"""Shared pytest fixtures/config for the ZORIN package.

Pins the headless matplotlib backend (so figure tests never open display
windows) and guarantees ``src/`` is importable regardless of how pytest is
invoked. No mocks anywhere — tests use real computation and real data only.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault("MPLBACKEND", "Agg")

# Ensure the package's src/ is importable even when pytest runs from a
# directory where `pythonpath` is not honoured.
_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


@pytest.fixture
def project_root() -> Path:
    """Path to the package root (parent of ``src/``/``tests/``)."""
    return Path(__file__).resolve().parents[1]
