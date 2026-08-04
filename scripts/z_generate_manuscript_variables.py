#!/usr/bin/env python3
"""Hydrate the ZORIN manuscript: compute tokens, resolve sections, render figures.

Strict by default (any unresolved ``{{TOKEN}}`` or missing metrics fails);
pass ``--allow-draft`` to fall back to partial resolution.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))  # noqa: E402

from a_view_to_a_kill import manuscript_variables as msv  # noqa: E402
from a_view_to_a_kill.figures import render_mission_figures  # noqa: E402

PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    require_outputs = "--allow-draft" not in args

    variables = msv.generate_variables(require_outputs=require_outputs)
    data_dir = PACKAGE_ROOT / "output" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "manuscript_variables.json").write_text(
        json.dumps(variables, indent=2, sort_keys=True), encoding="utf-8"
    )
    msv.resolve_manuscript_tree(variables, strict=require_outputs)
    figure_paths = render_mission_figures(PACKAGE_ROOT / "output" / "figures")
    print(f"Resolved {len(variables)} manuscript tokens -> output/data/manuscript_variables.json")
    print("Resolved manuscript -> output/manuscript/")
    for path in figure_paths:
        print(f"Figure: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
