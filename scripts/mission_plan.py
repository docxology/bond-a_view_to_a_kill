#!/usr/bin/env python3
"""ZORIN mission — produce the execution plan (phase: plan)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from a_view_to_a_kill.mission import MissionProvider  # noqa: E402


def main() -> int:
    provider = MissionProvider()
    plan = provider.plan(provider.brief())
    print("Mission plan steps:")
    for i, step in enumerate(plan.steps, 1):
        print(f"  {i}. {step.name}: {step.action} {step.params}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
