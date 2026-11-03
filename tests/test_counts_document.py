"""The counts document is generated, and this is the gate that says so.

``docs/_generated/COUNTS.md`` used to be an orphan: it claimed to be regenerated
while nothing regenerated it, and its re-measure command pointed at another
machine's checkout. The generator now exists (``render_counts_markdown`` in the
package, driven by ``scripts/z_generate_counts.py``), and these tests fail when
the file stops matching a fresh render, when the live inventories move, or when a
test is added without regenerating the file.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from a_view_to_a_kill import manuscript_variables as msv
from a_view_to_a_kill.mission import gadget_registry

PROJECT_ROOT = Path(__file__).resolve().parents[1]
COUNTS_PATH = PROJECT_ROOT / "docs" / "_generated" / "COUNTS.md"
SLUG = "a_view_to_a_kill"

_ROW_RE = re.compile(r"^\| ([^|]+?) \| (.+?) \|$", re.MULTILINE)
_BACKTICKED_RE = re.compile(r"`([^`]+)`")


def _rows() -> dict[str, str]:
    text = COUNTS_PATH.read_text(encoding="utf-8")
    rows = {key.strip(): value.strip() for key, value in _ROW_RE.findall(text)}
    # Positive control: the parse must have found the whole table, or every
    # comparison below would be comparing nothing to nothing.
    assert len(rows) >= 11, sorted(rows)
    return rows


def _live_gadgets() -> list[str]:
    return list(gadget_registry.gadgets_for(SLUG))


def _render_from(rows: dict[str, str], tests: int) -> str:
    return msv.render_counts_markdown(
        modules=msv.package_module_names(),
        gadgets=_live_gadgets(),
        tests=tests,
        coverage=rows["Line + branch coverage on `src/`"],
        skipped_failed=rows["Skipped / failed"],
        lowest_covered=rows["Lowest-covered module"],
        uncovered=rows["Uncovered statements remaining"],
        pure_modules=tuple(_BACKTICKED_RE.findall(rows["Pure domain modules"])),
        metric_layer=rows["Metric layer"],
        tokens=int(rows["Manuscript tokens resolved"]),
        figures=int(rows["Figures rendered"]),
    )


def test_counts_document_matches_a_fresh_render() -> None:
    rows = _rows()
    text = COUNTS_PATH.read_text(encoding="utf-8")
    tests = int(rows["Passing tests"])
    assert _render_from(rows, tests) == text, (
        "docs/_generated/COUNTS.md is not what render_counts_markdown writes; "
        "regenerate it with scripts/z_generate_counts.py"
    )
    # Positive control: the comparison above must be able to fail.
    assert _render_from(rows, tests + 1) != text


def test_counts_document_inventories_are_live() -> None:
    rows = _rows()
    modules = msv.package_module_names()
    assert rows["Modules at 100% coverage"].startswith(f"all {len(modules)}: "), rows[
        "Modules at 100% coverage"
    ]
    assert rows["Mission gadgets"] == ", ".join(
        f"`{gadget}`" for gadget in _live_gadgets()
    )


def test_recorded_test_count_is_the_collected_count() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    match = re.search(r"(\d+) tests? collected", result.stdout)
    assert match, result.stdout[-400:]  # positive control: the count was observed
    recorded = int(_rows()["Passing tests"])
    assert recorded == int(match.group(1)), (
        "the counts document records a test count the suite no longer collects; "
        "regenerate it with scripts/z_generate_counts.py"
    )


def test_unknown_counts_row_is_rejected() -> None:
    """The renderer's guard fires rather than silently dropping a mistyped row."""
    try:
        msv.render_counts_markdown(
            modules=msv.package_module_names(), gadgets=_live_gadgets(), not_a_row="x"
        )
    except ValueError as exc:
        assert "not_a_row" in str(exc)
    else:  # pragma: no cover - the guard must fire, this branch is the failure
        raise AssertionError("render_counts_markdown accepted an unknown row")


def test_unmeasured_test_count_states_the_gate_instead_of_a_number() -> None:
    """Omitting the measurement is a documented call, so the arm is exercised."""
    text = msv.render_counts_markdown(
        modules=msv.package_module_names(), gadgets=_live_gadgets()
    )
    assert "| Passing tests | not recorded — see the enforced gate below |" in text
