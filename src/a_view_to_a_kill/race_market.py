"""Race betting-market and cover-finance analytics.

The cover operation is financed by betting on the horse ZORIN controls. This
module models the betting market around the race card and turns it into a
deterministic finance problem:

* :func:`market_odds` — convert the model's true win probabilities into
  bookmaker decimal odds under an overround (vigorish), so the market's
  implied probabilities sum to ``overround`` (> 1).
* :func:`implied_probability` — the market-implied win chance ``1 / odds``.
* :func:`value_edge` — ``true_prob * odds - 1``, the expected profit per unit
  staked; positive means the market underprices the horse (a value bet).
* :func:`kelly_fraction` — the expected-log-growth-optimal fraction of the
  bankroll to stake when the bettor holds a true edge.
* :func:`cover_bankroll` — the full cover-finance plan for one boosted horse:
  true probability after a crafted boost, market-implied probability, the
  value edge, the Kelly stake in dollars, and the expected profit.

By coupling the boosted (manipulated) win probability with the *honest*
market odds, the model exposes precisely the asymmetry ZORIN exploits: a
boost that lifts the true chance well above the market's implied chance is a
large positive-edge bet — and simultaneously the anomaly that signal-detection
risk (in ``race_analytics``) would eventually flag.

Pure domain logic: imports only ``race_analytics``; no I/O, no randomness, no
``bond_api``.
"""

from __future__ import annotations

from dataclasses import dataclass

from a_view_to_a_kill import race_analytics as race

__all__ = [
    "KellyPosition",
    "CoverPlan",
    "market_odds",
    "implied_probability",
    "value_edge",
    "kelly_fraction",
    "cover_bankroll",
]


@dataclass(frozen=True)
class KellyPosition:
    """A single horse's betting position under a given market."""

    horse: str
    odds: float
    implied_probability: float
    value_edge: float
    kelly_fraction: float
    kelly_stake: float  # dollars
    expected_profit: float  # dollars


@dataclass(frozen=True)
class CoverPlan:
    """The deterministic cover-finance plan for one boosted horse."""

    horse: str
    true_probability: float  # after the craft-bought boost
    market_implied_probability: float
    value_edge: float
    kelly_fraction: float
    kelly_stake: float
    expected_profit: float


def market_odds(probabilities: dict[str, float], overround: float = 1.12) -> dict[str, float]:
    """Decimal odds per horse under bookmaker ``overround``.

    Implied market probabilities ``q_i = p_i * overround`` (summing to
    ``overround``), so decimal odds ``o_i = 1 / q_i``. A higher overround means
    a heavier margin (shorter odds) for the bookmaker.
    """
    if not isinstance(overround, (int, float)) or isinstance(overround, bool):
        raise ValueError("overround must be a number")
    if overround <= 1.0:
        raise ValueError("overround must be strictly greater than 1.0")
    if not probabilities:
        raise ValueError("probabilities must not be empty")
    total = sum(probabilities.values())
    if total <= 0:
        raise ValueError("probabilities must sum to a positive value")
    odds: dict[str, float] = {}
    for name, prob in probabilities.items():
        if prob < 0:
            raise ValueError(f"probability for {name!r} must be non-negative")
        implied = prob * overround / total if total else 0.0
        odds[name] = 1.0 / implied if implied > 0 else float("inf")
    return odds


def implied_probability(odds: float) -> float:
    """Market-implied win probability (``1 / odds``) for a decimal odd."""
    if not isinstance(odds, (int, float)) or isinstance(odds, bool):
        raise ValueError("odds must be a number")
    if odds <= 0:
        raise ValueError("odds must be positive")
    return float(1.0 / odds)


def value_edge(true_probability: float, odds: float) -> float:
    """Expected profit per unit staked: ``true_prob * odds - 1``.

    Positive when the true win chance exceeds the market-implied chance.
    """
    for value in (true_probability, odds):
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ValueError("true_probability and odds must be numbers")
    if not 0.0 <= true_probability <= 1.0:
        raise ValueError("true_probability must be within [0, 1]")
    if odds <= 0:
        raise ValueError("odds must be positive")
    return float(true_probability * odds - 1.0)


def kelly_fraction(true_probability: float, odds: float) -> float:
    """Kelly-criterion fraction of the bankroll to stake on a positive-edge bet.

    Returns 0.0 when there is no edge (``true_prob * odds <= 1``). The Kelly
    fraction maximizes the expected logarithm of bankroll growth and is
    computed on decimal odds as ``(p*o - 1) / (o - 1)``.
    """
    edge = value_edge(true_probability, odds)
    if edge <= 0.0:
        return 0.0
    return float(edge / (odds - 1.0))


def cover_bankroll(
    probabilities: dict[str, float],
    boosted: str,
    boost: float,
    bankroll: float,
    overround: float = 1.12,
) -> CoverPlan:
    """The cover-finance plan for ``boosted`` after a performance ``boost``.

    The true win probability is the softmax over *boosted* ratings; the market
    is built on the *honest* (un-boosted) probabilities — the asymmetry ZORIN
    exploits. Returns a :class:`CoverPlan` with the Kelly stake (in dollars,
    capped at the bankroll) and the expected profit.
    """
    if not isinstance(bankroll, (int, float)) or isinstance(bankroll, bool):
        raise ValueError("bankroll must be a number")
    if bankroll <= 0:
        raise ValueError("bankroll must be positive")
    if boosted not in probabilities:
        raise ValueError(f"unknown horse {boosted!r}")

    # true probabilities incorporate the craft-bought boost
    true_probs = probabilities
    boosted_probs = race.manipulated_probabilities(true_probs, boosted, boost)
    true_p = float(boosted_probs[boosted])

    # market is the honest, un-boosted book
    odds_map = market_odds(probabilities, overround)
    odds = odds_map[boosted]
    implied = implied_probability(odds)
    edge = value_edge(true_p, odds)
    kelly = kelly_fraction(true_p, odds)
    stake = min(float(kelly * bankroll), float(bankroll))
    expected_profit = float(edge * stake)

    return CoverPlan(
        horse=boosted,
        true_probability=true_p,
        market_implied_probability=implied,
        value_edge=edge,
        kelly_fraction=kelly,
        kelly_stake=stake,
        expected_profit=expected_profit,
    )
