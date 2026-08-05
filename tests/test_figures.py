"""Tests for the ZORIN deterministic figure renderers (figures/plots.py)."""

from __future__ import annotations

from pathlib import Path

from a_view_to_a_kill.figures import (
    render_acquisition_curve,
    render_choke_points,
    render_cover,
    render_flood,
    render_mission_figures,
    render_valley_impact,
)


def _assert_png(path: Path) -> None:
    assert path.is_file()
    assert path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    assert path.stat().st_size > 0


_ALL = ("choke_points.png", "flood_curve.png", "race_cover.png", "acquisition_curve.png", "valley_impact.png")


def test_render_mission_figures_writes_all_five(tmp_path: Path) -> None:
    paths = render_mission_figures(tmp_path)
    assert len(paths) == 5
    for name in _ALL:
        _assert_png(tmp_path / name)


def test_render_choke_points_single(tmp_path: Path) -> None:
    path = render_choke_points(tmp_path / "cp.png")
    _assert_png(path)


def test_render_flood_single(tmp_path: Path) -> None:
    path = render_flood(tmp_path / "flood.png")
    _assert_png(path)


def test_render_cover_single(tmp_path: Path) -> None:
    path = render_cover(tmp_path / "cover.png")
    _assert_png(path)


def test_render_acquisition_curve_single(tmp_path: Path) -> None:
    path = render_acquisition_curve(tmp_path / "acq.png")
    _assert_png(path)


def test_render_valley_impact_single(tmp_path: Path) -> None:
    path = render_valley_impact(tmp_path / "valley.png")
    _assert_png(path)


def test_renders_are_deterministic(tmp_path: Path) -> None:
    render_mission_figures(tmp_path)
    first = (tmp_path / "valley_impact.png").read_bytes()
    out2 = tmp_path / "second"
    render_mission_figures(out2)
    second = (out2 / "valley_impact.png").read_bytes()
    assert first == second
