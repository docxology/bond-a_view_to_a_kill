#!/usr/bin/env python3
"""Write the ZORIN live-counts document.

``docs/_generated/COUNTS.md`` is a generated artifact, and this is its generator:
the rendering lives in ``a_view_to_a_kill.manuscript_variables
.render_counts_markdown``, the live inventories are read off the package here, and
the drift gate that reads the file back is ``tests/test_counts_document.py``. Thin
by construction — bootstrap, call, write, print.

    uv run python scripts/z_generate_counts.py --tests 316 --coverage 100.00%

Anything omitted keeps the value recorded in the renderer's defaults, which are
dated there.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from a_view_to_a_kill import manuscript_variables as msv
from a_view_to_a_kill.mission import gadget_registry

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SLUG = "a_view_to_a_kill"
DEFAULT_OUT = PACKAGE_ROOT / "docs" / "_generated" / "COUNTS.md"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="write docs/_generated/COUNTS.md")
    parser.add_argument(
        "--tests", type=int, default=None, help="test count from a real run"
    )
    parser.add_argument("--coverage", default=None, help="coverage row from that run")
    parser.add_argument("--skipped-failed", default=None, help="skipped / failed row")
    parser.add_argument(
        "--lowest-covered", default=None, help="lowest-covered module row"
    )
    parser.add_argument("--uncovered", default=None, help="uncovered-statements row")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="output path")
    args = parser.parse_args(argv)

    overrides = {
        "coverage": args.coverage,
        "skipped_failed": args.skipped_failed,
        "lowest_covered": args.lowest_covered,
        "uncovered": args.uncovered,
    }
    modules = msv.package_module_names()
    gadgets = list(gadget_registry.gadgets_for(SLUG))
    text = msv.render_counts_markdown(
        modules=modules,
        gadgets=gadgets,
        tests=args.tests,
        **{key: value for key, value in overrides.items() if value is not None},
    )
    args.out.write_text(text, encoding="utf-8")
    print(
        f"Wrote {args.out.relative_to(PACKAGE_ROOT)}: {len(modules)} modules, "
        f"{len(gadgets)} gadgets, tests={args.tests}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
