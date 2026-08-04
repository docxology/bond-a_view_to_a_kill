"""Tests for the microchip supply-chain security graph (chip_supply_chain.py)."""

from __future__ import annotations

import pytest

from a_view_to_a_kill import chip_supply_chain as chip


# ---------------------------------------------------------------- datasets
def test_default_graph_is_valid_and_sized() -> None:
    chain = chip.build_default_supply_chain()
    assert chip.validate_graph(chain) is None
    assert len(chain.suppliers) == 12
    assert len(chain.links) == 18


def test_default_covers_all_stages() -> None:
    chain = chip.build_default_supply_chain()
    stages = {s.stage for s in chain.suppliers}
    assert stages == set(chip.STAGES)


# ---------------------------------------------------------------- validation
@pytest.mark.parametrize("bad", [("", 1.0), ("  ", 1.0)])
def test_supplier_rejects_blank_name(bad: tuple[str, float]) -> None:
    with pytest.raises(ValueError):
        chip.Supplier(name=bad[0], stage="wafer", capacity=bad[1])


def test_supplier_rejects_unknown_stage() -> None:
    with pytest.raises(ValueError):
        chip.Supplier("x", "smelting", 1.0)


@pytest.mark.parametrize("capacity", [0.0, -1.0])
def test_supplier_rejects_nonpositive_capacity(capacity: float) -> None:
    with pytest.raises(ValueError):
        chip.Supplier("x", "wafer", capacity)


def test_supplier_rejects_bool_capacity() -> None:
    with pytest.raises(ValueError):
        chip.Supplier("x", "wafer", True)  # type: ignore[arg-type]


def test_graph_rejects_duplicate_names() -> None:
    with pytest.raises(ValueError):
        chip.SupplyChain(
            suppliers=(chip.Supplier("a", "wafer", 1.0), chip.Supplier("a", "wafer", 2.0)),
            links=(),
        )


def test_graph_rejects_self_loop() -> None:
    with pytest.raises(ValueError):
        chip.SupplyChain(
            suppliers=(chip.Supplier("a", "wafer", 1.0), chip.Supplier("b", "fabrication", 1.0)),
            links=(("a", "a"),),
        )


def test_graph_rejects_unknown_node_in_link() -> None:
    with pytest.raises(ValueError):
        chip.SupplyChain(
            suppliers=(chip.Supplier("a", "wafer", 1.0),),
            links=(("a", "ghost"),),
        )


def test_graph_rejects_backward_stage_flow() -> None:
    with pytest.raises(ValueError):
        chip.SupplyChain(
            suppliers=(chip.Supplier("a", "wafer", 1.0), chip.Supplier("b", "fabrication", 1.0)),
            links=(("b", "a"),),
        )


# ---------------------------------------------------------------- market share / HHI
def test_market_share_sums_to_one_per_stage() -> None:
    chain = chip.build_default_supply_chain()
    for stage in chip.STAGES:
        shares = chip.market_share(chain, stage)
        assert sum(shares.values()) == pytest.approx(1.0)
    assert sum(chip.market_share(chain).values()) == pytest.approx(1.0)


def test_market_share_unknown_stage_raises() -> None:
    with pytest.raises(ValueError):
        chip.market_share(chip.build_default_supply_chain(), "smelting")


def test_hhi_single_firm_is_maximum() -> None:
    chain = chip.SupplyChain(
        suppliers=(chip.Supplier("only", "wafer", 10.0),),
        links=(),
    )
    assert chip.hhi(chain, "wafer") == pytest.approx(10000.0)


def test_hhi_two_equal_firms() -> None:
    chain = chip.SupplyChain(
        suppliers=(chip.Supplier("a", "wafer", 1.0), chip.Supplier("b", "wafer", 1.0)),
        links=(),
    )
    # (0.5^2 + 0.5^2) * 10000 = 5000
    assert chip.hhi(chain, "wafer") == pytest.approx(5000.0)


def test_hhi_default_is_bounded() -> None:
    h = chip.hhi(chip.build_default_supply_chain())
    assert 0.0 <= h <= 10000.0


# ---------------------------------------------------------------- betweenness
def test_betweenness_path_marks_middle_as_choke() -> None:
    chain = chip.SupplyChain(
        suppliers=(
            chip.Supplier("a", "wafer", 1.0),
            chip.Supplier("b", "fabrication", 1.0),
            chip.Supplier("c", "assembly", 1.0),
        ),
        links=(("a", "b"), ("b", "c")),
    )
    bc = chip.betweenness_centrality(chain)
    assert bc["b"] == pytest.approx(0.5)
    assert bc["a"] == pytest.approx(0.0)


def test_betweenness_sources_have_zero() -> None:
    chain = chip.build_default_supply_chain()
    bc = chip.betweenness_centrality(chain)
    for supplier in chain.suppliers:
        if supplier.stage == "wafer":
            assert bc[supplier.name] == pytest.approx(0.0)


def test_top_choke_points_ranked_and_limited() -> None:
    top = chip.top_choke_points(chip.build_default_supply_chain(), 3)
    assert len(top) == 3
    values = [v for _, v in top]
    assert values == sorted(values, reverse=True)


@pytest.mark.parametrize("k", [0, -1, 1.5, "3"])
def test_top_choke_points_rejects_bad_k(k: object) -> None:
    with pytest.raises(ValueError):
        chip.top_choke_points(chip.build_default_supply_chain(), k)  # type: ignore[arg-type]


# ---------------------------------------------------------------- dependence / cascade
def test_single_source_dependence_marks_sole_supplier() -> None:
    chain = chip.SupplyChain(
        suppliers=(
            chip.Supplier("a", "wafer", 1.0),
            chip.Supplier("b", "fabrication", 1.0),
            chip.Supplier("c", "assembly", 1.0),
        ),
        links=(("a", "b"), ("b", "c")),
    )
    dep = chip.single_source_dependence(chain)
    assert dep["b"] == ("a",)
    assert dep["c"] == ("b",)


def test_cascade_removing_all_wafer_sources_starves_everything() -> None:
    chain = chip.build_default_supply_chain()
    sources = {s.name for s in chain.suppliers if s.stage == "wafer"}
    starved, fraction = chip.cascade_starved(chain, sources)
    non_wafer = {s.name for s in chain.suppliers if s.stage != "wafer"}
    assert starved == non_wafer
    assert fraction == pytest.approx(len(non_wafer) / len(chain.suppliers))


def test_cascade_sole_supplier_break_in_small_chain() -> None:
    chain = chip.SupplyChain(
        suppliers=(
            chip.Supplier("a", "wafer", 1.0),
            chip.Supplier("b", "fabrication", 1.0),
            chip.Supplier("c", "assembly", 1.0),
        ),
        links=(("a", "b"), ("b", "c")),
    )
    starved, fraction = chip.cascade_starved(chain, ["a"])
    assert starved == {"b", "c"}
    assert fraction == pytest.approx(2 / 3)


def test_cascade_empty_removal_is_benign() -> None:
    starved, fraction = chip.cascade_starved(chip.build_default_supply_chain(), [])
    assert starved == set()
    assert fraction == 0.0


# ---------------------------------------------------------------- monopoly attack
def test_monopoly_share_increases_with_acquisition() -> None:
    chain = chip.build_default_supply_chain()
    before = chip.monopoly_share(chain)["fabrication"]
    after = chip.monopoly_share(chain, ["amd_fab", "nec_fab"])["fabrication"]
    assert after > before
    assert after > 0.5  # ZORIN corners fabrication


def test_monopoly_share_unknown_acquired_raises() -> None:
    with pytest.raises(ValueError):
        chip.monopoly_share(chip.build_default_supply_chain(), ["ghost"])


def test_post_elimination_hhi_rises_with_acquisition() -> None:
    chain = chip.build_default_supply_chain()
    before = chip.post_elimination_hhi(chain)
    after = chip.post_elimination_hhi(chain, ["amd_fab", "nec_fab"])
    assert after > before
