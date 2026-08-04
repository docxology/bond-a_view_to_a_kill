#!/usr/bin/env python3
"""ZORIN mission — execute the plan and report outcomes (phase: execute)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from a_view_to_a_kill.mission import MissionProvider  # noqa: E402


def main() -> int:
    provider = MissionProvider()
    outcome = provider.execute(provider.plan(provider.brief()))
    print(f"Outcome: success={outcome.success}")
    print(
        f"Provenance: version={outcome.provenance.package_version} "
        f"seed={outcome.provenance.seed} hash={outcome.provenance.input_hash}"
    )
    for group, metrics in outcome.results.items():
        if group == "steps_completed":
            continue
        print(f"[{group}]")
        for key, value in metrics.items():
            print(f"  {key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
