"""Regeneration determinism: two real runs must write identical bytes.

This is the gate behind the package's byte-identical-rerun claim
(`manuscript/02_methodology.md`, `manuscript/06_reproducibility.md`,
`AGENTS.md`, `README.md`). It is deliberately built so that it *can fail*:

* No clock is injected. The old `generate_variables(now=...)` override made a
  determinism test trivially green — a fixed input gives a fixed output for
  any function whatsoever — while a live `datetime.now(timezone.utc)` stamp
  moved `output/manuscript/05_experimental_setup.md` and
  `output/data/manuscript_variables.json` on every single run. The claim was
  false for months under a passing suite. That is the failure mode these tests
  exist to make impossible.
* Real wall-clock time elapses between the two runs, more than the one-second
  resolution the old stamp used, so any reintroduced clock reading changes
  value between run 1 and run 2 and the byte comparison goes red.
* The subprocess test drives the committed orchestrator
  (`scripts/z_generate_manuscript_variables.py`) exactly as a reader would,
  in two fresh interpreters, and compares every persisted artifact:
  `.json` payload, resolved `.md` sections, and rendered `.png` figures.

Scope of the claim these tests bind: identical source tree + identical
interpreter => identical artifact bytes. The only environment-derived token is
`PYTHON_VERSION`, which is constant for a given toolchain; nothing else in the
pipeline reads anything outside the repository.

No mocks: real subprocesses, real files, real elapsed time.
"""

from __future__ import annotations

import ast
import hashlib
import subprocess
import sys
import time
from pathlib import Path

from a_view_to_a_kill import manuscript_variables as msv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GENERATOR = PROJECT_ROOT / "scripts" / "z_generate_manuscript_variables.py"

#: Longer than the one-second resolution of any plausible ISO timestamp stamp,
#: so a reintroduced clock reading is guaranteed to differ between the runs.
CLOCK_GAP_SECONDS = 1.2

#: The artifact classes the byte-identical claim covers.
ARTIFACT_SUFFIXES = (".json", ".md", ".png")


def _digest_tree(root: Path) -> dict[str, str]:
    """Map each artifact's path (relative to ``root``) to its SHA-256."""
    digests: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix in ARTIFACT_SUFFIXES:
            digests[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return digests


def _run_generator() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(GENERATOR)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )


def test_two_real_generator_runs_write_byte_identical_artifacts() -> None:
    """Run the committed generator twice; every persisted byte must match.

    This is the end-to-end form of the claim: it exercises the real script,
    the real config, the real output directory, and two separate processes.
    """
    output_root = PROJECT_ROOT / "output"

    first = _run_generator()
    assert first.returncode == 0, first.stderr
    before = _digest_tree(output_root)
    assert before, "generator produced no artifacts to compare"

    time.sleep(CLOCK_GAP_SECONDS)

    second = _run_generator()
    assert second.returncode == 0, second.stderr
    after = _digest_tree(output_root)

    assert sorted(before) == sorted(after), "the two runs produced different artifact sets"
    drifted = sorted(name for name in before if before[name] != after[name])
    assert not drifted, (
        "regeneration is not byte-identical; these artifacts changed between two runs "
        f"of {GENERATOR.name} with no source change: {drifted}"
    )


def test_two_variable_computations_across_elapsed_time_are_equal() -> None:
    """The token mapping itself must not move with the wall clock.

    Narrower and faster than the subprocess test, and it localises a failure:
    if this one goes red the offending value is a token, not a figure or a
    file-writing side effect.
    """
    first = msv.generate_variables()
    time.sleep(CLOCK_GAP_SECONDS)
    second = msv.generate_variables()

    drifted = sorted(key for key in first if first[key] != second[key])
    assert first.keys() == second.keys()
    assert not drifted, f"these tokens are not a function of committed inputs: {drifted}"


def test_resolved_manuscript_is_byte_identical_across_elapsed_time(tmp_path: Path) -> None:
    """Resolve the manuscript tree twice into two directories and diff bytes."""
    first_dir = tmp_path / "run1"
    second_dir = tmp_path / "run2"

    msv.resolve_manuscript_tree(msv.generate_variables(), output_dir=first_dir)
    time.sleep(CLOCK_GAP_SECONDS)
    msv.resolve_manuscript_tree(msv.generate_variables(), output_dir=second_dir)

    left = _digest_tree(first_dir)
    right = _digest_tree(second_dir)
    assert left, "no manuscript sections were resolved"
    assert left == right, "the resolved manuscript is not byte-identical across reruns"


#: Clock reads that would reintroduce the defect, as dotted call names.
BANNED_CLOCK_CALLS = frozenset(
    {
        "datetime.now",
        "datetime.datetime.now",
        "datetime.utcnow",
        "datetime.datetime.utcnow",
        "date.today",
        "datetime.date.today",
        "time.time",
        "time.time_ns",
        "time.monotonic",
        "time.localtime",
        "time.gmtime",
        "time.strftime",
    }
)

PIPELINE_MODULES = (
    Path("src/a_view_to_a_kill/manuscript_variables.py"),
    Path("src/a_view_to_a_kill/metrics.py"),
    Path("src/a_view_to_a_kill/figures/plots.py"),
    Path("scripts/z_generate_manuscript_variables.py"),
)


def _dotted_name(node: ast.expr) -> str:
    """Render an attribute/name chain (``a.b.c``) as a dotted string."""
    parts: list[str] = []
    current: ast.expr = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id)
    return ".".join(reversed(parts))


def _clock_calls(source: str) -> list[tuple[int, str]]:
    """Every banned clock call in ``source``, as (lineno, dotted name)."""
    return [
        (node.lineno, _dotted_name(node.func))
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Call) and _dotted_name(node.func) in BANNED_CLOCK_CALLS
    ]


def test_no_wall_clock_is_read_anywhere_in_the_manuscript_pipeline() -> None:
    """Source-level guard: no pipeline module may *call* a clock.

    Complements the byte comparisons above — a future edit that reintroduces a
    timestamp fails here by name and line, instead of only surfacing as an
    opaque hash mismatch. The scan is AST-based, not a substring grep, so
    prose and comments that discuss the removed `datetime.now()` do not trip
    it and a call cannot hide behind whitespace or an alias chain.
    """
    offenders: list[str] = []
    for relative in PIPELINE_MODULES:
        module = PROJECT_ROOT / relative
        assert module.is_file(), f"pipeline module missing: {relative}"
        for lineno, call in _clock_calls(module.read_text(encoding="utf-8")):
            offenders.append(f"{relative}:{lineno}: {call}()")
    assert not offenders, f"wall-clock read in the deterministic manuscript pipeline: {offenders}"


def test_the_clock_guard_detects_a_real_clock_call() -> None:
    """Positive control: the AST scan must actually bite.

    Without this, `test_no_wall_clock_is_read_anywhere_in_the_manuscript_pipeline`
    could pass because the detector is broken rather than because the pipeline
    is clean — the same class of green-by-construction gate that let the
    original breach through.
    """
    reintroduced = "from datetime import datetime, timezone\nstamp = datetime.now(timezone.utc).isoformat()\n"
    assert _clock_calls(reintroduced) == [(2, "datetime.now")]
    # ...and prose mentioning the call is not a call.
    assert _clock_calls('"""We do not call datetime.now() here."""\n') == []
