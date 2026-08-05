"""The pure core must import and compute with ``bond_api`` unavailable.

Every doc in this package claims the pure core, the metric layer, the figure
renderers, and the manuscript pipeline are importable in the fallback where
the ``bond-api`` path dependency is missing. Prose cannot enforce that, so
this file *proves* it: each test launches a fresh interpreter in which a real
:class:`importlib.abc.MetaPathFinder` refuses to resolve ``bond_api``, then
runs the real computation there.

No mocking framework is involved — the blocker is an ordinary import hook, and
the numbers checked are the genuine outputs of the pure core. The positive
control (``test_mission_adapter_needs_bond_api``) confirms the blocker really
does bite, so a passing fallback test cannot be green by construction.
"""

from __future__ import annotations

import json
import subprocess
import sys
import textwrap
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SRC = PACKAGE_ROOT / "src"

#: A real meta-path finder that makes ``bond_api`` unimportable, simulating a
#: checkout where the path dependency was never installed.
BLOCKER = """
import sys


class _BlockBondApi:
    def find_module(self, fullname, path=None):  # legacy API, harmless
        return None

    def find_spec(self, fullname, path=None, target=None):
        if fullname == "bond_api" or fullname.startswith("bond_api."):
            raise ImportError("bond_api is unavailable (fallback test)")
        return None


for _name in [m for m in sys.modules if m == "bond_api" or m.startswith("bond_api.")]:
    del sys.modules[_name]
sys.meta_path.insert(0, _BlockBondApi())
sys.path.insert(0, {src!r})
"""


def _run_without_bond_api(body: str) -> subprocess.CompletedProcess[str]:
    script = BLOCKER.format(src=str(SRC)) + textwrap.dedent(body)
    return subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        cwd=str(PACKAGE_ROOT),
        check=False,
    )


def test_blocker_actually_blocks_bond_api() -> None:
    """Positive control: the import hook must really make bond_api fail."""
    proc = _run_without_bond_api(
        """
        try:
            import bond_api  # noqa: F401
        except ImportError as exc:
            print("BLOCKED:" + str(exc))
        else:
            print("NOT_BLOCKED")
        """
    )
    assert proc.returncode == 0, proc.stderr
    assert "BLOCKED:" in proc.stdout
    assert "NOT_BLOCKED" not in proc.stdout


def test_pure_core_imports_and_computes_without_bond_api() -> None:
    proc = _run_without_bond_api(
        """
        import json
        from a_view_to_a_kill import metrics

        payload = metrics.run_mission_metrics()
        print("RESULT:" + json.dumps(sorted(payload)))
        """
    )
    assert proc.returncode == 0, proc.stderr
    groups = json.loads(proc.stdout.split("RESULT:")[1])
    assert groups == sorted(("chip", "flood", "race", "acquisition", "valley", "market"))


def test_manuscript_pipeline_resolves_without_bond_api(tmp_path: Path) -> None:
    proc = _run_without_bond_api(
        f"""
        from a_view_to_a_kill import manuscript_variables as msv

        variables = msv.generate_variables()
        out_dir, resolved = msv.resolve_manuscript_tree(variables, output_dir={str(tmp_path)!r})
        print("SECTIONS:" + str(len(resolved)))
        print("HHI:" + variables["SC_HHI_BEFORE"])
        """
    )
    assert proc.returncode == 0, proc.stderr
    assert "SECTIONS:9" in proc.stdout
    # the same value the in-process (bond_api-available) run produces
    from a_view_to_a_kill import manuscript_variables as msv

    assert f"HHI:{msv.generate_variables()['SC_HHI_BEFORE']}" in proc.stdout
    assert (tmp_path / "03_results.md").exists()


def test_figures_render_without_bond_api(tmp_path: Path) -> None:
    proc = _run_without_bond_api(
        f"""
        from a_view_to_a_kill.figures import render_mission_figures

        paths = render_mission_figures({str(tmp_path)!r})
        print("FIGURES:" + str(len(paths)))
        """
    )
    assert proc.returncode == 0, proc.stderr
    assert "FIGURES:5" in proc.stdout
    assert sorted(p.name for p in tmp_path.glob("*.png")) == [
        "acquisition_curve.png",
        "choke_points.png",
        "flood_curve.png",
        "race_cover.png",
        "valley_impact.png",
    ]


def test_mission_adapter_needs_bond_api() -> None:
    """Negative control: the adapter is the one module that must fail."""
    proc = _run_without_bond_api(
        """
        try:
            from a_view_to_a_kill import mission  # noqa: F401
        except ImportError as exc:
            print("ADAPTER_BLOCKED:" + str(exc))
        else:
            print("ADAPTER_IMPORTED")
        """
    )
    assert proc.returncode == 0, proc.stderr
    assert "ADAPTER_BLOCKED:" in proc.stdout


def test_mission_is_still_reachable_as_a_package_attribute() -> None:
    """Lazy loading must not change the public shape the suite consumes."""
    import a_view_to_a_kill
    from a_view_to_a_kill import mission as direct

    assert a_view_to_a_kill.mission is direct
    assert "mission" in dir(a_view_to_a_kill)
    assert direct.MissionProvider.film == "a_view_to_a_kill"


def test_unknown_package_attribute_still_raises() -> None:
    import a_view_to_a_kill

    try:
        a_view_to_a_kill.no_such_module  # noqa: B018
    except AttributeError as exc:
        assert "no_such_module" in str(exc)
    else:  # pragma: no cover - the lazy hook must not swallow typos
        raise AssertionError("expected AttributeError for an unknown attribute")
