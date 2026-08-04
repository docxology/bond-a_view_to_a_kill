#!/usr/bin/env python3
"""ZORIN mission — run reconnaissance for a goal (phase: recon)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from a_view_to_a_kill.mission import MissionProvider  # noqa: E402
from bond_api.protocol import ReconRequest  # noqa: E402

DEFAULT_GOAL = "assess the ZORIN monopoly, flood, and cover operation"


def main(argv: list[str] | None = None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    goal = args[0] if args else DEFAULT_GOAL
    provider = MissionProvider()
    report = provider.recon(ReconRequest(goal))
    print(f"Recon report for goal: {goal}")
    for finding in report.findings:
        print(f"  [{finding.label}] {finding.detail}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
