"""Tests for the mine-flood -> surface-fab valley coupling (valley_impact.py)."""

from __future__ import annotations

import pytest

from a_view_to_a_kill import mine_flood as flood
from a_view_to_a_kill import valley_impact as valley


def _scenario() -> tuple[flood.MineNetwork, flood.FloodResult, flood.FloodParams]:
    mine = flood.build_default_mine()
    params = flood.FloodParams(ingress_rate=10.0, horizon=900.0, dt=1.0)
    return mine, flood.simulate_flood(mine, ("adit",), params), params


# ---------------------------------------------------------------- validation
@pytest.mark.parametrize("bad", [("", 1.0, "c", 1.0, 0.5), ("  ", 1.0, "c", 1.0, 0.5)])
def test_fab_rejects_blank_name(bad: tuple[object, ...]) -> None:
    with pytest.raises(ValueError):
        valley.SurfaceFab(bad[0], bad[1], bad[2], bad[3], bad[4])  # type: ignore[arg-type]


@pytest.mark.parametrize("capacity", [0.0, -1.0])
def test_fab_rejects_nonpositive_capacity(capacity: float) -> None:
    with pytest.raises(ValueError):
        valley.SurfaceFab("f", capacity, "c", 1.0, 0.5)


def test_fab_rejects_blank_chamber() -> None:
    with pytest.raises(ValueError):
        valley.SurfaceFab("f", 1.0, "  ", 1.0, 0.5)


@pytest.mark.parametrize("leakage", [-0.1, 1.5])
def test_fab_rejects_out_of_range_leakage(leakage: float) -> None:
    with pytest.raises(ValueError):
        valley.SurfaceFab("f", 1.0, "c", 1.0, leakage)


def test_fab_rejects_non_numeric_foundation() -> None:
    with pytest.raises(ValueError):
        valley.SurfaceFab("f", 1.0, "c", "high", 0.5)  # type: ignore[arg-type]


def test_default_valley_has_five_fabs() -> None:
    assert len(valley.build_default_valley()) == 5


# ---------------------------------------------------------------- levels
def test_chamber_level_at_unknown_raises() -> None:
    mine, sim, _ = _scenario()
    with pytest.raises(ValueError):
        valley.chamber_level_at(mine, sim, "ghost", 100.0)


@pytest.mark.parametrize("t", [-1.0, "x"])
def test_chamber_level_at_rejects_bad_t(t: object) -> None:
    mine, sim, _ = _scenario()
    with pytest.raises(ValueError):
        valley.chamber_level_at(mine, sim, "adit", t)  # type: ignore[arg-type]


def test_chamber_level_at_rises_as_chamber_floods() -> None:
    mine, sim, _ = _scenario()
    level_start = valley.chamber_level_at(mine, sim, "gallery_north", 100.0)
    level_end = valley.chamber_level_at(mine, sim, "gallery_north", 900.0)
    assert level_end >= level_start
    assert level_start > 0.0


def test_fab_water_table_is_leakage_scaled_level() -> None:
    mine, sim, _ = _scenario()
    fab = valley.build_default_valley()[0]  # intel_fab, leakage 0.85
    level = valley.chamber_level_at(mine, sim, fab.chamber, 900.0)
    assert valley.fab_water_table(mine, sim, fab, 900.0) == pytest.approx(level * fab.leakage)


# ---------------------------------------------------------------- impact
def test_fab_inoperable_at_victim_fab() -> None:
    mine, sim, _ = _scenario()
    fabs = {f.name: f for f in valley.build_default_valley()}
    at = valley.fab_inoperable_at(mine, sim, fabs["intel_fab"])
    assert at is not None
    assert 0.0 < at <= 900.0


def test_fab_inoperable_at_survivor_is_none() -> None:
    mine, sim, _ = _scenario()
    fabs = {f.name: f for f in valley.build_default_valley()}
    # ZORIN's own fab is coupled with low leakage to a high foundation.
    assert valley.fab_inoperable_at(mine, sim, fabs["zorin_fab"]) is None


def test_zero_leakage_fab_never_inoperable() -> None:
    mine, sim, _ = _scenario()
    fab = valley.SurfaceFab("isolated", 100.0, "vault", 10.0, 0.0)
    assert valley.fab_inoperable_at(mine, sim, fab) is None


def test_capacity_loss_default_is_non_trivial() -> None:
    mine, sim, params = _scenario()
    loss = valley.valley_capacity_loss(mine, sim, valley.build_default_valley(), params.horizon)
    assert 0.0 < loss < 1.0
    assert loss == pytest.approx(0.5833333333333334)


def test_capacity_loss_starts_at_zero_and_monotone() -> None:
    mine, sim, _ = _scenario()
    fabs = valley.build_default_valley()
    assert valley.valley_capacity_loss(mine, sim, fabs, 0.0) == 0.0
    earlier = valley.valley_capacity_loss(mine, sim, fabs, 500.0)
    later = valley.valley_capacity_loss(mine, sim, fabs, 900.0)
    assert later >= earlier


def test_capacity_loss_empty_fabs_is_zero() -> None:
    mine, sim, _ = _scenario()
    assert valley.valley_capacity_loss(mine, sim, [], 900.0) == 0.0


def test_valley_report_summary() -> None:
    mine, sim, params = _scenario()
    report = valley.valley_report(mine, sim, valley.build_default_valley(), params.horizon)
    assert report["inoperable"] == 3
    assert report["capacity_loss"] == pytest.approx(0.5833333333333334)
    assert set(report["victims"]) == {"intel_fab", "amd_fab", "silicon_valley_fab"}
    assert set(report["survivors"]) == {"zorin_fab", "nec_fab"}
    assert report["total_capacity"] == pytest.approx(3000.0)
    assert "water_table" in report["fabs"]["intel_fab"]
