"""Tests for the monopoly acquisition optimizer (acquisition.py)."""

from __future__ import annotations

import pytest

from a_view_to_a_kill import acquisition as acq
from a_view_to_a_kill import chip_supply_chain as chip


def _default() -> chip.SupplyChain:
    return chip.build_default_supply_chain()


def _small_chain() -> chip.SupplyChain:
    """Three fabricators; the biggest (highest-capacity) is clearly best."""
    return chip.SupplyChain(
        suppliers=(
            chip.Supplier("wa", "wafer", 1000.0),
            chip.Supplier("fa", "fabrication", 100.0, "zorin"),
            chip.Supplier("fb", "fabrication", 300.0),
            chip.Supplier("fc", "fabrication", 200.0),
            chip.Supplier("fd", "fabrication", 600.0),
        ),
        links=(("wa", "fa"), ("wa", "fb"), ("wa", "fc"), ("wa", "fd")),
    )


def test_acquireable_firms_are_independent_fabricators() -> None:
    firms = acq.acquireable_firms(_default())
    assert firms == ("amd_fab", "intel_fab", "nec_fab")


def test_unknown_objective_raises() -> None:
    with pytest.raises(ValueError):
        acq.acquisition_score(_default(), ("amd_fab",), "market_value")


@pytest.mark.parametrize("objective", ["hhi", "fab_share"])
def test_acquisition_score_matches_objective(objective: str) -> None:
    chain = _default()
    score = acq.acquisition_score(chain, ("amd_fab",), objective)
    assert score > 0.0


def test_optimal_budget_zero_is_baseline() -> None:
    chain = _default()
    best, score = acq.optimal_acquisition(chain, 0, "hhi")
    assert best == ()
    assert score == pytest.approx(acq.acquisition_score(chain, (), "hhi"))


@pytest.mark.parametrize("budget", [-1, 4, 1.5])
def test_optimal_raises_on_bad_budget(budget: object) -> None:
    with pytest.raises(ValueError):
        acq.optimal_acquisition(_default(), budget)  # type: ignore[arg-type]


def test_optimal_is_deterministic() -> None:
    a = acq.optimal_acquisition(_default(), 2, "hhi")
    b = acq.optimal_acquisition(_default(), 2, "hhi")
    assert a == b


def test_optimal_default_budget_two() -> None:
    best, score = acq.optimal_acquisition(_default(), 2, "hhi")
    assert best == ("intel_fab", "nec_fab")
    assert score == pytest.approx(acq.acquisition_score(_default(), best, "hhi"))


def test_greedy_never_beats_optimal() -> None:
    chain = _default()
    for budget in range(0, len(acq.acquireable_firms(chain)) + 1):
        _, optimal = acq.optimal_acquisition(chain, budget, "hhi")
        _, greedy = acq.greedy_acquisition(chain, budget, "hhi")
        assert greedy == pytest.approx(optimal) or greedy < optimal


def test_small_chain_picks_highest_capacity_fab() -> None:
    # budget 1 of {fb:300, fc:200, fd:600}: exhaustive picks fd (largest share).
    best, _ = acq.optimal_acquisition(_small_chain(), 1, "hhi")
    assert best == ("fd",)


def test_improvement_gain_nonnegative() -> None:
    improved = acq.improvement(_default(), 2, "hhi")
    assert improved.objective == "hhi"
    assert improved.gain == pytest.approx(improved.score - improved.baseline)
    assert improved.gain >= 0.0
    assert improved.score > improved.baseline


def test_greedy_spends_its_whole_budget() -> None:
    """The greedy plan must contain exactly ``budget`` distinct firms.

    A sentinel-initialised gain accumulator (``best_gain = -1.0``) silently
    truncated the plan whenever every candidate gain fell below the sentinel;
    this pins the invariant for every reachable budget.
    """
    chain = _default()
    firms = acq.acquireable_firms(chain)
    for budget in range(0, len(firms) + 1):
        acquired, _ = acq.greedy_acquisition(chain, budget, "hhi")
        assert len(acquired) == budget
        assert len(set(acquired)) == budget
        assert set(acquired) <= set(firms)
        assert list(acquired) == sorted(acquired)


def test_greedy_is_deterministic_and_scores_its_own_plan() -> None:
    chain = _default()
    first = acq.greedy_acquisition(chain, 2, "fab_share")
    second = acq.greedy_acquisition(chain, 2, "fab_share")
    assert first == second
    acquired, score = first
    assert score == pytest.approx(acq.acquisition_score(chain, acquired, "fab_share"))


def test_greedy_full_budget_equals_buying_everything() -> None:
    chain = _default()
    firms = acq.acquireable_firms(chain)
    acquired, score = acq.greedy_acquisition(chain, len(firms), "hhi")
    assert acquired == firms
    assert score == pytest.approx(acq.acquisition_score(chain, firms, "hhi"))


def test_improvement_preserves_optimum() -> None:
    improved = acq.improvement(_default(), 2, "hhi")
    best, score = acq.optimal_acquisition(_default(), 2, "hhi")
    assert improved.acquired == best
    assert improved.score == pytest.approx(score)
