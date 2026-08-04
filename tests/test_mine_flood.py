"""Tests for the flood-the-mine water-ingress model (mine_flood.py)."""

from __future__ import annotations

import numpy as np
import pytest

from a_view_to_a_kill import mine_flood as flood


def _one_chamber(volume: float = 900.0, area: float = 45.0) -> flood.MineNetwork:
    return flood.MineNetwork(
        chambers=(flood.Chamber("only", volume, area, elevation=0.0),),
        tunnels=(),
    )


# ---------------------------------------------------------------- validation
@pytest.mark.parametrize("bad", [("", 900.0), ("  ", 900.0)])
def test_chamber_rejects_blank_name(bad: tuple[str, float]) -> None:
    with pytest.raises(ValueError):
        flood.Chamber(bad[0], bad[1], 45.0, 0.0)


@pytest.mark.parametrize("volume", [0.0, -5.0])
def test_chamber_rejects_nonpositive_volume(volume: float) -> None:
    with pytest.raises(ValueError):
        flood.Chamber("c", volume, 45.0, 0.0)


@pytest.mark.parametrize("area", [0.0, -1.0])
def test_chamber_rejects_nonpositive_area(area: float) -> None:
    with pytest.raises(ValueError):
        flood.Chamber("c", 900.0, area, 0.0)


@pytest.mark.parametrize("cross", [0.0, -1.0])
def test_tunnel_rejects_nonpositive_cross_area(cross: float) -> None:
    with pytest.raises(ValueError):
        flood.Tunnel("t", "a", "b", cross)


def test_network_rejects_duplicate_chamber() -> None:
    with pytest.raises(ValueError):
        flood.MineNetwork(
            chambers=(flood.Chamber("a", 1.0, 1.0, 0.0), flood.Chamber("a", 1.0, 1.0, 0.0)),
            tunnels=(),
        )


def test_network_rejects_unknown_tunnel_endpoint() -> None:
    with pytest.raises(ValueError):
        flood.MineNetwork(
            chambers=(flood.Chamber("a", 1.0, 1.0, 0.0),),
            tunnels=(flood.Tunnel("t", "a", "ghost", 1.0),),
        )


def test_network_rejects_self_loop_tunnel() -> None:
    with pytest.raises(ValueError):
        flood.MineNetwork(
            chambers=(flood.Chamber("a", 1.0, 1.0, 0.0),),
            tunnels=(flood.Tunnel("t", "a", "a", 1.0),),
        )


def test_network_rejects_duplicate_tunnel() -> None:
    with pytest.raises(ValueError):
        flood.MineNetwork(
            chambers=(
                flood.Chamber("a", 1.0, 1.0, 0.0),
                flood.Chamber("b", 1.0, 1.0, 0.0),
            ),
            tunnels=(
                flood.Tunnel("t1", "a", "b", 1.0),
                flood.Tunnel("t2", "b", "a", 1.0),
            ),
        )


@pytest.mark.parametrize("field,value", [("ingress_rate", 0.0), ("horizon", -1.0), ("dt", 0.0), ("discharge", -2.0)])
def test_flood_params_rejects_nonpositive(field: str, value: float) -> None:
    kwargs = {"ingress_rate": 1.0, "horizon": 10.0, "dt": 1.0, "discharge": 0.6}
    kwargs[field] = value
    with pytest.raises(ValueError):
        flood.FloodParams(**kwargs)  # type: ignore[arg-type]


# ---------------------------------------------------------------- ingress
def test_ingress_flow_splits_evenly() -> None:
    mine = flood.build_default_mine()
    params = flood.FloodParams(ingress_rate=10.0, horizon=10.0)
    flows = flood.ingress_flows(mine, ("adit", "shaft_a"), params)
    assert flows["adit"] == pytest.approx(5.0)
    assert flows["shaft_a"] == pytest.approx(5.0)


def test_ingress_flow_empty_raises() -> None:
    with pytest.raises(ValueError):
        flood.ingress_flows(flood.build_default_mine(), (), flood.FloodParams(1.0, 10.0))


def test_ingress_flow_unknown_chamber_raises() -> None:
    with pytest.raises(ValueError):
        flood.ingress_flows(flood.build_default_mine(), ("ghost",), flood.FloodParams(1.0, 10.0))


# ---------------------------------------------------------------- simulation
def test_simulation_conserves_mass() -> None:
    mine = flood.build_default_mine()
    params = flood.FloodParams(ingress_rate=10.0, horizon=900.0, dt=1.0)
    result = flood.simulate_flood(mine, ("adit",), params)
    assert flood.water_balance_error(result) < 1e-9
    assert result.times.shape[0] == result.volumes.shape[1]
    assert result.volumes.shape[0] == len(mine.chambers)


def test_simulation_is_deterministic() -> None:
    mine = flood.build_default_mine()
    params = flood.FloodParams(ingress_rate=10.0, horizon=300.0, dt=0.5)
    a = flood.simulate_flood(mine, ("adit", "shaft_b"), params)
    b = flood.simulate_flood(mine, ("adit", "shaft_b"), params)
    assert np.array_equal(a.volumes, b.volumes)


def test_single_chamber_fill_time_matches_closed_form() -> None:
    chamber = flood.Chamber("only", volume=900.0, area=45.0, elevation=0.0)
    mine = flood.MineNetwork(chambers=(chamber,), tunnels=())
    params = flood.FloodParams(ingress_rate=9.0, horizon=200.0, dt=1.0)
    result = flood.simulate_flood(mine, ("only",), params)
    flood_time = flood.flooded_at(result, "only")
    expected = flood.closed_form_fill_time(chamber, 9.0)
    assert flood_time is not None
    assert abs(flood_time - expected) <= params.dt


def test_closed_form_fill_time_rejects_bad_rate() -> None:
    with pytest.raises(ValueError):
        flood.closed_form_fill_time(flood.Chamber("c", 900.0, 45.0, 0.0), 0.0)


# ---------------------------------------------------------------- queries
def test_flooded_fraction_ranges_and_monotonicity() -> None:
    mine = flood.build_default_mine()
    params = flood.FloodParams(ingress_rate=10.0, horizon=900.0, dt=1.0)
    result = flood.simulate_flood(mine, ("adit",), params)
    assert flood.flooded_fraction(result, 0.0) == 0.0
    f_mid = flood.flooded_fraction(result, 450.0)
    f_end = flood.flooded_fraction(result, 900.0)
    assert 0.0 <= f_mid <= f_end <= 1.0
    assert flood.flooded_fraction(result, 100000.0) == f_end  # clamped past horizon


@pytest.mark.parametrize("t", [-1.0, "x"])
def test_flooded_fraction_rejects_bad_t(t: object) -> None:
    mine = flood.build_default_mine()
    params = flood.FloodParams(ingress_rate=10.0, horizon=900.0)
    result = flood.simulate_flood(mine, ("adit",), params)
    with pytest.raises(ValueError):
        flood.flooded_fraction(result, t)  # type: ignore[arg-type]


def test_flooded_at_unknown_chamber_raises() -> None:
    mine = flood.build_default_mine()
    params = flood.FloodParams(ingress_rate=10.0, horizon=900.0)
    result = flood.simulate_flood(mine, ("adit",), params)
    with pytest.raises(ValueError):
        flood.flooded_at(result, "ghost")


def test_flooded_at_low_chamber_floods() -> None:
    mine = flood.build_default_mine()
    params = flood.FloodParams(ingress_rate=10.0, horizon=900.0, dt=1.0)
    result = flood.simulate_flood(mine, ("adit",), params)
    assert flood.flooded_at(result, "vault") is not None


def test_critical_ingress_is_deterministic_and_one_of_candidates() -> None:
    mine = flood.build_default_mine()
    params = flood.FloodParams(ingress_rate=10.0, horizon=900.0, dt=1.0)
    best, fraction = flood.critical_ingress(mine, ("adit", "shaft_a", "shaft_b"), params)
    assert best in ("adit", "shaft_a", "shaft_b")
    assert 0.0 <= fraction <= 1.0
    again, _ = flood.critical_ingress(mine, ("adit", "shaft_a", "shaft_b"), params)
    assert again == best


def test_critical_ingress_empty_raises() -> None:
    with pytest.raises(ValueError):
        flood.critical_ingress(flood.build_default_mine(), (), flood.FloodParams(1.0, 10.0))


def test_critical_ingress_unknown_candidate_raises() -> None:
    with pytest.raises(ValueError):
        flood.critical_ingress(flood.build_default_mine(), ("ghost",), flood.FloodParams(1.0, 10.0))


def test_default_scenario_floods_partially() -> None:
    mine = flood.build_default_mine()
    params = flood.FloodParams(ingress_rate=10.0, horizon=900.0, dt=1.0)
    result = flood.simulate_flood(mine, ("adit",), params)
    fraction = flood.flooded_fraction(result, params.horizon)
    assert 0.0 < fraction < 1.0
