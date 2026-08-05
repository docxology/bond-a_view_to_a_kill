"""Tests for the racing betting-market / cover-finance model (race_market.py)."""

from __future__ import annotations

import pytest

from a_view_to_a_kill import race_analytics as race
from a_view_to_a_kill import race_market as mkt


def _probs() -> dict[str, float]:
    ratings = race.form_ratings(race.FORM_TABLE)
    return {name: hr.rating for name, hr in ratings.items()}


# ---------------------------------------------------------------- odds
def test_market_odds_implied_sum_is_overround() -> None:
    probs = _probs()
    odds = mkt.market_odds(probs, 1.12)
    implied_total = sum(1.0 / o for o in odds.values())
    assert implied_total == pytest.approx(1.12)
    assert all(o > 1.0 for o in odds.values())


def test_market_odds_higher_prob_shorter_odds() -> None:
    odds = mkt.market_odds({"a": 0.6, "b": 0.4})
    assert odds["a"] < odds["b"]


@pytest.mark.parametrize("overround", [1.0, 0.9, -1.0, "x"])
def test_market_odds_rejects_bad_overround(overround: object) -> None:
    with pytest.raises(ValueError):
        mkt.market_odds(_probs(), overround)  # type: ignore[arg-type]


def test_market_odds_rejects_empty_and_negative() -> None:
    with pytest.raises(ValueError):
        mkt.market_odds({})
    with pytest.raises(ValueError):
        mkt.market_odds({"a": -0.1})


# ---------------------------------------------------------------- implied / edge / kelly
def test_implied_probability_is_reciprocal() -> None:
    assert mkt.implied_probability(4.0) == pytest.approx(0.25)


@pytest.mark.parametrize("odds", [-1.0, 0.0, "x"])
def test_implied_probability_rejects_bad_odds(odds: object) -> None:
    with pytest.raises(ValueError):
        mkt.implied_probability(odds)  # type: ignore[arg-type]


def test_value_edge_formula() -> None:
    # fair: p*o = 1 -> edge 0
    assert mkt.value_edge(0.25, 4.0) == pytest.approx(0.0)
    # underpriced: p*o > 1 -> positive edge
    assert mkt.value_edge(0.3, 4.0) == pytest.approx(0.2)


@pytest.mark.parametrize("prob", [-0.1, 1.5])
def test_value_edge_rejects_out_of_range_prob(prob: float) -> None:
    with pytest.raises(ValueError):
        mkt.value_edge(prob, 4.0)


def test_kelly_fraction_zero_without_edge() -> None:
    assert mkt.kelly_fraction(0.25, 4.0) == pytest.approx(0.0)  # fair
    assert mkt.kelly_fraction(0.2, 4.0) == pytest.approx(0.0)  # negative edge


def test_kelly_fraction_formula_with_edge() -> None:
    # p=0.5, o=3 -> edge = 0.5 -> fraction = 0.5/(3-1) = 0.25
    assert mkt.kelly_fraction(0.5, 3.0) == pytest.approx(0.25)


# ---------------------------------------------------------------- cover bankroll
def test_cover_bankroll_unknown_horse_raises() -> None:
    with pytest.raises(ValueError):
        mkt.cover_bankroll(_probs(), "ghost", 0.2, 100_000.0)


@pytest.mark.parametrize("bankroll", [0.0, -100.0])
def test_cover_bankroll_rejects_bad_bankroll(bankroll: float) -> None:
    with pytest.raises(ValueError):
        mkt.cover_bankroll(_probs(), "Pegasus", 0.2, bankroll)


def test_cover_bankroll_boosts_true_prob_above_implied() -> None:
    plan = mkt.cover_bankroll(_probs(), "Pegasus", 0.2, 100_000.0)
    assert plan.true_probability > plan.market_implied_probability
    assert plan.value_edge > 0.0
    assert 0.0 <= plan.kelly_fraction < 1.0
    assert plan.kelly_stake == pytest.approx(plan.kelly_fraction * 100_000.0)
    assert plan.kelly_stake <= 100_000.0
    assert plan.expected_profit == pytest.approx(plan.value_edge * plan.kelly_stake)


def test_cover_bankroll_no_boost_low_true_probability() -> None:
    plan = mkt.cover_bankroll(_probs(), "Pegasus", 0.0, 100_000.0)
    assert plan.true_probability == pytest.approx(race.win_probabilities(_probs())["Pegasus"])


def test_cover_bankroll_is_deterministic() -> None:
    a = mkt.cover_bankroll(_probs(), "Pegasus", 0.2, 100_000.0)
    b = mkt.cover_bankroll(_probs(), "Pegasus", 0.2, 100_000.0)
    assert a == b
