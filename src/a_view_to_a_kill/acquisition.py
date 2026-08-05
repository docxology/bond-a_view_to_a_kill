"""Monopoly acquisition optimizer — which firms should ZORIN buy?

ZORIN's monopoly scheme is a *selection* problem as much as a structural one:
given a limited acquisition budget (how many competitor fabricators he can
buy), which subset best corners the market? This module answers it two ways:

* :func:`optimal_acquisition` — exhaustive search over every budget-sized
  subset of the acquireable independent fabricators, scoring each by a chosen
  objective (market-wide post-elimination HHI, or ZORIN's fabrication capacity
  share), with deterministic tie-breaking (lexicographically smallest set).
* :func:`greedy_acquisition` — a deterministic hill-climbing baseline that
  adds, one at a time, the firm yielding the largest score gain.

Because the exhaustive search is optimal, ``greedy <= optimal`` always; the
gap between them is the (avoidable) cost of a naive acquisition strategy.
:func:`improvement` reports the objective gain of the optimal budget over
buying nothing.

Pure domain logic — imports only the (equally pure) ``chip_supply_chain``
module; no I/O, no randomness, no ``bond_api``.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Callable

from a_view_to_a_kill import chip_supply_chain as chip

__all__ = [
    "AcquisitionResult",
    "OBJECTIVES",
    "acquireable_firms",
    "acquisition_score",
    "optimal_acquisition",
    "greedy_acquisition",
    "improvement",
]

#: Supported acquisition objectives: value that ``acquisition_score`` returns.
OBJECTIVES = ("hhi", "fab_share")


@dataclass(frozen=True)
class AcquisitionResult:
    """A chosen acquisition plan and its measured objective.

    Attributes:
        acquired: The inductor firms ZORIN buys, in deterministic order.
        objective: The objective key this plan was scored on.
        score: The objective value for this plan.
        baseline: The objective value for buying nothing.
    """

    acquired: tuple[str, ...]
    objective: str
    score: float
    baseline: float

    @property
    def gain(self) -> float:
        """Score improvement over the no-acquisition baseline (>= 0)."""
        return self.score - self.baseline


def acquireable_firms(chain: chip.SupplyChain) -> tuple[str, ...]:
    """The independent (non-ZORIN) fabrication firms ZORIN could buy, in
    deterministic name order."""
    names = sorted(s.name for s in chain.suppliers if s.stage == "fabrication" and s.owner != "zorin")
    return tuple(names)


def _selected(chain: chip.SupplyChain, objective: str) -> Callable[[tuple[str, ...]], float]:
    if objective not in OBJECTIVES:
        raise ValueError(f"unknown objective {objective!r}; expected one of {OBJECTIVES}")
    if objective == "hhi":
        return lambda acquired: chip.post_elimination_hhi(chain, acquired)
    return lambda acquired: float(chip.monopoly_share(chain, acquired)["fabrication"])


def acquisition_score(chain: chip.SupplyChain, acquired: tuple[str, ...], objective: str) -> float:
    """The objective value (``hhi`` or ``fab_share``) of acquiring ``acquired``
    firms from ``chain``."""
    score_func = _selected(chain, objective)
    return float(score_func(acquired))


def _validate_budget(chain: chip.SupplyChain, budget: int) -> None:
    if not isinstance(budget, int) or isinstance(budget, bool):
        raise ValueError("budget must be an integer")
    if budget < 0:
        raise ValueError("budget must be non-negative")
    count = len(acquireable_firms(chain))
    if budget > count:
        raise ValueError(f"budget {budget} exceeds {count} acquireable fabrication firms")


def optimal_acquisition(
    chain: chip.SupplyChain,
    budget: int,
    objective: str = "hhi",
) -> tuple[tuple[str, ...], float]:
    """Exhaustively find the budget-sized subset maximizing ``objective``.

    Deterministic: ties resolve to the lexicographically smallest subset so
    repeated calls return an identical plan. Returns ``(acquired, score)``.
    """
    _validate_budget(chain, budget)
    score_func = _selected(chain, objective)
    firms = acquireable_firms(chain)
    baseline = score_func(())
    if budget == 0:
        return (), float(baseline)
    best_score = -1.0
    best_set: tuple[str, ...] = ()
    for combo in combinations(firms, budget):
        score = score_func(combo)
        if score > best_score or (score == best_score and not best_set):
            best_score = float(score)
            best_set = combo
    return best_set, best_score


def greedy_acquisition(
    chain: chip.SupplyChain,
    budget: int,
    objective: str = "hhi",
) -> tuple[tuple[str, ...], float]:
    """Deterministic greedy baseline: repeatedly add the firm with the largest
    score gain, breaking name-ties by order."""
    _validate_budget(chain, budget)
    score_func = _selected(chain, objective)
    firms = acquireable_firms(chain)
    current: tuple[str, ...] = ()
    score = float(score_func(()))
    for _ in range(budget):
        best_gain = -1.0
        best_firm: str | None = None
        for firm in firms:
            if firm in current:
                continue
            candidate = tuple(sorted(current + (firm,)))
            candidate_score = score_func(candidate)
            gain = float(candidate_score) - score
            if gain > best_gain or (gain == best_gain and (best_firm is None or firm < best_firm)):
                best_gain = gain
                best_firm = firm
        if best_firm is None:
            break
        current = tuple(sorted(current + (best_firm,)))
        score = float(score_func(current))
    return current, score


def improvement(
    chain: chip.SupplyChain,
    budget: int,
    objective: str = "hhi",
) -> AcquisitionResult:
    """Full acquisition-plan report: optimal plan, its score, and the baseline.

    ``AcquisitionResult.gain`` is the non-negative objective improvement over
    buying nothing; ``greedy <= optimal`` holds by construction.
    """
    acquired, score = optimal_acquisition(chain, budget, objective)
    baseline = acquisition_score(chain, (), objective)
    return AcquisitionResult(acquired=acquired, objective=objective, score=score, baseline=baseline)
