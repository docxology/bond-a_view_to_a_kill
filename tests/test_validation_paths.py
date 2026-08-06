"""Error-path and boundary coverage for every pure module.

The happy paths are covered by the per-module test files. This file closes the
defensive branches: every ``ValueError`` a caller can actually trigger, plus
the reachable early-return boundaries. Each test passes a real bad value to a
real function — no mocking, no patching.

Some defensive branches in the pure core are *unreachable* by construction and
are deliberately not chased here (a zero-capacity market cannot exist because
``Supplier`` rejects non-positive capacity; a zero-chamber network cannot exist
because ``MineNetwork`` rejects an empty tuple). Those are recorded in
``TODO.md`` as dead defensive code rather than papered over with a test that
cannot fail.
"""

from __future__ import annotations

import pytest

from a_view_to_a_kill import chip_supply_chain as chip
from a_view_to_a_kill import mine_flood as flood
from a_view_to_a_kill import race_analytics as race
from a_view_to_a_kill import race_market as mkt
from a_view_to_a_kill import valley_impact as valley

# --------------------------------------------------------------------------
# chip_supply_chain
# --------------------------------------------------------------------------


def test_supplier_rejects_blank_owner() -> None:
    with pytest.raises(ValueError, match="owner must be a non-empty string"):
        chip.Supplier("f", "fabrication", 100.0, "   ")


def test_supply_chain_rejects_empty_suppliers() -> None:
    with pytest.raises(ValueError, match="suppliers must be a non-empty tuple"):
        chip.SupplyChain(suppliers=(), links=())


def test_supply_chain_rejects_non_tuple_links() -> None:
    supplier = chip.Supplier("w", "wafer", 10.0)
    with pytest.raises(ValueError, match="links must be a tuple"):
        chip.SupplyChain(suppliers=(supplier,), links=["w", "w"])  # type: ignore[arg-type]


def test_supply_chain_rejects_link_to_unknown_upstream() -> None:
    supplier = chip.Supplier("w", "wafer", 10.0)
    with pytest.raises(ValueError, match="unknown upstream supplier"):
        chip.SupplyChain(suppliers=(supplier,), links=(("ghost", "w"),))


def test_market_share_rejects_unknown_stage() -> None:
    with pytest.raises(ValueError, match="unknown stage"):
        chip.market_share(chip.build_default_supply_chain(), "packaging")


def test_monopoly_share_rejects_unknown_acquired_firm() -> None:
    with pytest.raises(ValueError, match="acquired firms unknown"):
        chip.monopoly_share(chip.build_default_supply_chain(), ("ghost_fab",))


def test_betweenness_normalization_on_a_two_node_graph() -> None:
    """n <= 2 takes the unit-denominator branch and must stay in [0, 1]."""
    chain = chip.SupplyChain(
        suppliers=(chip.Supplier("w", "wafer", 10.0), chip.Supplier("f", "fabrication", 10.0)),
        links=(("w", "f"),),
    )
    centrality = chip.betweenness_centrality(chain)
    assert set(centrality) == {"w", "f"}
    assert all(0.0 <= v <= 1.0 for v in centrality.values())


def test_betweenness_ignores_longer_non_shortest_paths() -> None:
    """Nodes on a longer parallel route earn no credit for the pair it skips.

    Two routes run from the wafer source to the distributor: a three-hop path
    through `fab_long` -> `asm`, and a two-hop shortcut through `fab_short`.
    Only the shortcut is a shortest `w -> dist` path, so that pair must credit
    `fab_short` alone. This is the branch Brandes' algorithm takes when a
    neighbor has already been reached at a *shorter* distance; an
    implementation that credited every path (not just shortest ones) would
    hand `fab_long` the extra pair and push it above `fab_short`.

    Each interior node still lies on exactly one shortest path pair, so all
    three tie — and the endpoints, which are never intermediate, score zero.
    """
    chain = chip.SupplyChain(
        suppliers=(
            chip.Supplier("w", "wafer", 10.0),
            chip.Supplier("fab_long", "fabrication", 10.0),
            chip.Supplier("fab_short", "fabrication", 10.0),
            chip.Supplier("asm", "assembly", 10.0),
            chip.Supplier("dist", "distribution", 10.0),
        ),
        links=(
            ("w", "fab_long"),
            ("fab_long", "asm"),
            ("asm", "dist"),
            ("w", "fab_short"),
            ("fab_short", "dist"),
        ),
    )
    centrality = chip.betweenness_centrality(chain)
    assert centrality["w"] == 0.0
    assert centrality["dist"] == 0.0
    assert centrality["fab_short"] > 0.0
    # the long route gains nothing from the w -> dist pair it does not serve
    assert centrality["fab_long"] == pytest.approx(centrality["fab_short"])
    assert centrality["asm"] == pytest.approx(centrality["fab_short"])


def test_monopoly_share_is_zero_for_a_stage_with_no_firms() -> None:
    """A market missing a whole stage takes the empty-stage branch."""
    chain = chip.SupplyChain(
        suppliers=(chip.Supplier("w", "wafer", 10.0), chip.Supplier("f", "fabrication", 10.0, "zorin")),
        links=(("w", "f"),),
    )
    shares = chip.monopoly_share(chain, ())
    assert shares["assembly"] == 0.0
    assert shares["distribution"] == 0.0
    assert shares["fabrication"] == pytest.approx(1.0)


# --------------------------------------------------------------------------
# mine_flood
# --------------------------------------------------------------------------


def _tiny_mine() -> flood.MineNetwork:
    return flood.MineNetwork(
        chambers=(
            flood.Chamber("adit", 100.0, 10.0, 100.0),
            flood.Chamber("deep", 100.0, 10.0, 90.0),
        ),
        tunnels=(flood.Tunnel("t1", "adit", "deep", 1.0),),
    )


@pytest.mark.parametrize("field", ["volume", "area", "elevation"])
def test_chamber_rejects_non_numeric_fields(field: str) -> None:
    kwargs: dict[str, object] = {"name": "c", "volume": 10.0, "area": 2.0, "elevation": 1.0}
    kwargs[field] = "deep"
    with pytest.raises(ValueError, match=f"{field} must be a number"):
        flood.Chamber(**kwargs)  # type: ignore[arg-type]


def test_tunnel_rejects_blank_name() -> None:
    with pytest.raises(ValueError, match="Tunnel.name must be a non-empty string"):
        flood.Tunnel("  ", "a", "b", 1.0)


def test_tunnel_rejects_non_numeric_cross_area() -> None:
    with pytest.raises(ValueError, match="cross_area must be a number"):
        flood.Tunnel("t", "a", "b", "wide")  # type: ignore[arg-type]


def test_mine_network_rejects_empty_chambers() -> None:
    with pytest.raises(ValueError, match="chambers must be a non-empty tuple"):
        flood.MineNetwork(chambers=(), tunnels=())


def test_mine_network_rejects_non_tuple_tunnels() -> None:
    with pytest.raises(ValueError, match="tunnels must be a tuple"):
        flood.MineNetwork(chambers=(flood.Chamber("c", 1.0, 1.0, 0.0),), tunnels=[])  # type: ignore[arg-type]


def test_mine_network_rejects_duplicate_tunnel_names() -> None:
    with pytest.raises(ValueError, match="duplicate tunnel names"):
        flood.MineNetwork(
            chambers=(
                flood.Chamber("a", 1.0, 1.0, 1.0),
                flood.Chamber("b", 1.0, 1.0, 0.0),
            ),
            tunnels=(flood.Tunnel("t", "a", "b", 1.0), flood.Tunnel("t", "b", "a", 1.0)),
        )


@pytest.mark.parametrize("field", ["ingress_rate", "horizon", "dt", "discharge"])
def test_flood_params_rejects_non_numeric_fields(field: str) -> None:
    kwargs: dict[str, object] = {"ingress_rate": 1.0, "horizon": 10.0, "dt": 1.0, "discharge": 0.6}
    kwargs[field] = "fast"
    with pytest.raises(ValueError, match=f"{field} must be a number"):
        flood.FloodParams(**kwargs)  # type: ignore[arg-type]


def test_flooded_at_rejects_unknown_chamber() -> None:
    sim = flood.simulate_flood(_tiny_mine(), ("adit",), flood.FloodParams(1.0, 10.0))
    with pytest.raises(ValueError, match="unknown chamber"):
        flood.flooded_at(sim, "ghost")


def test_flooded_at_returns_none_when_a_chamber_never_fills() -> None:
    """A horizon far too short to fill anything must return None, not 0.0."""
    sim = flood.simulate_flood(_tiny_mine(), ("adit",), flood.FloodParams(0.001, 5.0))
    assert flood.flooded_at(sim, "deep") is None
    assert flood.flooded_fraction(sim, 5.0) == 0.0


def test_closed_form_fill_time_validates_rate() -> None:
    chamber = flood.Chamber("c", 100.0, 10.0, 0.0)
    with pytest.raises(ValueError, match="rate must be a number"):
        flood.closed_form_fill_time(chamber, "fast")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="rate must be positive"):
        flood.closed_form_fill_time(chamber, 0.0)
    assert flood.closed_form_fill_time(chamber, 10.0) == pytest.approx(10.0)


def test_isolated_chamber_takes_the_no_flow_branch() -> None:
    """A tunnel with zero head difference moves no water but must stay stable."""
    level_mine = flood.MineNetwork(
        chambers=(
            flood.Chamber("a", 100.0, 10.0, 50.0),
            flood.Chamber("b", 100.0, 10.0, 50.0),
        ),
        tunnels=(flood.Tunnel("t", "a", "b", 1.0),),
    )
    sim = flood.simulate_flood(level_mine, ("a",), flood.FloodParams(1.0, 20.0))
    assert flood.water_balance_error(sim) < 1e-9


# --------------------------------------------------------------------------
# race_analytics
# --------------------------------------------------------------------------


def test_race_result_rejects_non_integer_race_index() -> None:
    with pytest.raises(ValueError, match="race_index must be an integer"):
        race.RaceResult("Pegasus", 1.5, 8.0, "firm", 126.0, 100.0)  # type: ignore[arg-type]


def test_race_result_rejects_negative_race_index() -> None:
    with pytest.raises(ValueError, match="race_index must be non-negative"):
        race.RaceResult("Pegasus", -1, 8.0, "firm", 126.0, 100.0)


@pytest.mark.parametrize("field,position", [("distance", 2), ("weight", 4), ("time_s", 5)])
def test_race_result_rejects_non_numeric_measurements(field: str, position: int) -> None:
    args: list[object] = ["Pegasus", 0, 8.0, "firm", 126.0, 100.0]
    args[position] = "quick"
    with pytest.raises(ValueError, match=f"{field} must be a number"):
        race.RaceResult(*args)  # type: ignore[arg-type]


def test_form_ratings_rejects_non_numeric_halflife() -> None:
    with pytest.raises(ValueError, match="halflife must be a number"):
        race.form_ratings(race.FORM_TABLE, "two")  # type: ignore[arg-type]


def test_win_probabilities_rejects_non_numeric_temperature() -> None:
    ratings = {"a": 1.0, "b": 2.0}
    with pytest.raises(ValueError, match="temperature must be a number"):
        race.win_probabilities(ratings, "hot")  # type: ignore[arg-type]


def test_manipulated_probabilities_rejects_non_numeric_boost() -> None:
    ratings = {"a": 1.0, "b": 2.0}
    with pytest.raises(ValueError, match="boost must be a number"):
        race.manipulated_probabilities(ratings, "a", "lots")  # type: ignore[arg-type]


def test_detection_risk_validates_every_argument() -> None:
    with pytest.raises(ValueError, match="boost must be a number"):
        race.detection_risk(race.FORM_TABLE, "Pegasus", "lots", 0.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="boost must be non-negative"):
        race.detection_risk(race.FORM_TABLE, "Pegasus", -0.1, 0.5)
    with pytest.raises(ValueError, match="natural_sigma must be a number"):
        race.detection_risk(race.FORM_TABLE, "Pegasus", 0.2, "wide")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="threshold must be a number"):
        race.detection_risk(race.FORM_TABLE, "Pegasus", 0.2, 0.5, "high")  # type: ignore[arg-type]


# --------------------------------------------------------------------------
# race_market
# --------------------------------------------------------------------------


def test_market_odds_rejects_negative_probability() -> None:
    with pytest.raises(ValueError, match="must be non-negative"):
        mkt.market_odds({"a": 0.6, "b": -0.1}, 1.12)


def test_value_edge_validates_its_arguments() -> None:
    with pytest.raises(ValueError, match="must be numbers"):
        mkt.value_edge("even", 2.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="odds must be positive"):
        mkt.value_edge(0.5, 0.0)


def test_cover_bankroll_rejects_non_numeric_bankroll() -> None:
    with pytest.raises(ValueError, match="bankroll must be a number"):
        mkt.cover_bankroll({"Pegasus": 1.0, "Other": 0.5}, "Pegasus", 0.2, "lots")  # type: ignore[arg-type]


# --------------------------------------------------------------------------
# valley_impact
# --------------------------------------------------------------------------


def test_surface_fab_rejects_non_numeric_capacity() -> None:
    with pytest.raises(ValueError, match="capacity must be a number"):
        valley.SurfaceFab("f", "big", "c", 50.0, 0.5)  # type: ignore[arg-type]


def test_surface_fab_rejects_non_numeric_leakage() -> None:
    with pytest.raises(ValueError, match="leakage must be a number"):
        valley.SurfaceFab("f", 100.0, "c", 50.0, "leaky")  # type: ignore[arg-type]


def test_chamber_level_rejects_a_chamber_absent_from_the_network() -> None:
    """The result knows the chamber but the network passed in does not."""
    mine = _tiny_mine()
    sim = flood.simulate_flood(mine, ("adit",), flood.FloodParams(1.0, 10.0))
    other = flood.MineNetwork(
        chambers=(flood.Chamber("elsewhere", 10.0, 1.0, 0.0),),
        tunnels=(),
    )
    with pytest.raises(ValueError, match="not in network"):
        valley.chamber_level_at(other, sim, "adit", 1.0)


def test_valley_capacity_loss_is_zero_for_an_empty_fab_list() -> None:
    mine = _tiny_mine()
    sim = flood.simulate_flood(mine, ("adit",), flood.FloodParams(1.0, 10.0))
    assert valley.valley_capacity_loss(mine, sim, (), 10.0) == 0.0


def test_post_elimination_hhi_rejects_unknown_acquired_firm() -> None:
    """Contract parity with ``monopoly_share``: a typo'd acquired firm must
    raise, not be silently ignored (silent ignoring would quietly change the
    reported post-elimination HHI while ``monopoly_share`` raised)."""
    with pytest.raises(ValueError, match="acquired firms unknown"):
        chip.post_elimination_hhi(chip.build_default_supply_chain(), ("ghost_fab",))
