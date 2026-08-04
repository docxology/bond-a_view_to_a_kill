#!/usr/bin/env python3
"""ZORIN mission — print the mission brief (phase: brief)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from a_view_to_a_kill.mission import MissionProvider  # noqa: E402


def main() -> int:
    provider = MissionProvider()
    brief = provider.brief()
    print(f"Mission brief — {brief.film} ({brief.codename})")
    print("Objectives:")
    for i, objective in enumerate(brief.objectives, 1):
        print(f"  {i}. {objective}")
    print("Assets:")
    for asset in brief.assets:
        print(f"  - {asset.kind}: {asset.name} {asset.payload}")
    print("Constraints:")
    for constraint in brief.constraints:
        print(f"  - {constraint.kind}: {constraint.detail}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
