#!/usr/bin/env python3
"""ZORIN mission — run the full flow and deliver the debrief (phase: debrief)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from a_view_to_a_kill.mission import MissionProvider  # noqa: E402
from bond_api.protocol import ReconRequest, run_mission  # noqa: E402

DEFAULT_GOAL = "assess the ZORIN monopoly, flood, and cover operation"


def main() -> int:
    provider = MissionProvider()
    debrief = run_mission(provider, ReconRequest(DEFAULT_GOAL))
    outcome = debrief.outcome
    print(f"Debrief — {provider.film} / {provider.brief().codename}")
    print(f"Success: {outcome.success} | seed {outcome.provenance.seed}")
    print(f"Flood water-balance error: {outcome.results['flood']['water_balance_error']:.2e}")
    print(f"Cover detection risk: {outcome.results['race']['detection_risk']:.3f}")
    print("Lessons:")
    for lesson in debrief.lessons:
        print(f"  - {lesson}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
