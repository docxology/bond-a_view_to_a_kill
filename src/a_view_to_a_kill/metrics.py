"""ZORIN mission scenario parameters and computed metric groups (pure).

This module holds everything the mission *computes* — the fixed scenario
parameters and the six deterministic metric groups — with **no** ``bond_api``
import. :mod:`a_view_to_a_kill.mission` re-exports every public name here and
adds only the protocol adapter (``MissionProvider``) and the gadget registry.

The split exists so the documented fallback is actually true: the pure core,
:mod:`a_view_to_a_kill.manuscript_variables`, and
:mod:`a_view_to_a_kill.figures` can all run when the ``bond-api`` path
dependency is unavailable. Before the split they imported ``mission``, which
imports ``bond_api.protocol`` at module level, so the fallback silently did
not hold — ``tests/test_bond_api_fallback.py`` now pins it.

Nothing here does I/O, draws randomness, or reads the wall clock: two calls to
:func:`run_mission_metrics` return equal payloads.
"""

from __future__ import annotations

from typing import Any

from a_view_to_a_kill import acquisition as acq
from a_view_to_a_kill import chip_supply_chain as chip
from a_view_to_a_kill import mine_flood as flood
from a_view_to_a_kill import race_analytics as race
from a_view_to_a_kill import race_market as mkt
from a_view_to_a_kill import valley_impact as valley

__all__ = [
    "PACKAGE_VERSION",
    "SEED",
    "FLOOD_PARAMS",
    "ACQUIRED_FIRMS",
    "COVER_BOOST",
    "COVER_SIGMA",
    "ACQUISITION_BUDGET",
    "COVER_BANKROLL",
    "METRIC_GROUPS",
    "chip_metrics",
    "flood_metrics",
    "race_metrics",
    "acquisition_metrics",
    "valley_metrics",
    "market_metrics",
    "run_mission_metrics",
]

#: Package software version, surfaced in provenance.
PACKAGE_VERSION = "0.1.0"

#: Deterministic mission seed (the film's release year disables randomness).
SEED = 1985

#: Default flood scenario parameters for the execute stage.
FLOOD_PARAMS = flood.FloodParams(ingress_rate=10.0, horizon=900.0, dt=1.0)

#: Firms ZORIN acquires to complete his silicon-valley monopoly.
ACQUIRED_FIRMS = ("amd_fab", "nec_fab")

#: Cover-operation parameters for Pegasus in the execute stage.
COVER_BOOST = 0.2
COVER_SIGMA = 0.5

#: Acquisition budget (number of independent fabricators to buy) and the
#: cover-operation bankroll backing the betting market.
ACQUISITION_BUDGET = 2
COVER_BANKROLL = 100_000.0

#: The metric-group keys :func:`run_mission_metrics` always populates.
METRIC_GROUPS = ("chip", "flood", "race", "acquisition", "valley", "market")


def chip_metrics() -> dict[str, Any]:
    """Computed supply-chain security metrics for the ZORIN monopoly attack."""
    chain = chip.build_default_supply_chain()
    return {
        "nodes": len(chain.suppliers),
        "links": len(chain.links),
        "hhi_before": chip.hhi(chain),
        "hhi_after": chip.post_elimination_hhi(chain, ACQUIRED_FIRMS),
        "zorin_fab_share": chip.monopoly_share(chain, ACQUIRED_FIRMS)["fabrication"],
        "top_choke_points": chip.top_choke_points(chain, 3),
        "cascade_starved_fraction": chip.cascade_starved(chain, list(ACQUIRED_FIRMS))[1],
    }


def flood_metrics() -> dict[str, Any]:
    """Computed mine-flood water-ingress metrics for the ZORIN sabotage."""
    mine = flood.build_default_mine()
    sim = flood.simulate_flood(mine, ("adit",), FLOOD_PARAMS)
    return {
        "chambers": len(mine.chambers),
        "tunnels": len(mine.tunnels),
        "total_volume": float(sum(c.volume for c in mine.chambers)),
        "flooded_fraction": flood.flooded_fraction(sim, FLOOD_PARAMS.horizon),
        "vault_flood_time": flood.flooded_at(sim, "vault"),
        "critical_ingress": flood.critical_ingress(mine, ("adit", "shaft_a", "shaft_b"), FLOOD_PARAMS),
        "water_balance_error": flood.water_balance_error(sim),
    }


def race_metrics() -> dict[str, Any]:
    """Computed race-form analytics and cover-operation risk metrics."""
    ratings = race.form_ratings(race.FORM_TABLE)
    rating_map = {name: hr.rating for name, hr in ratings.items()}
    probs = race.win_probabilities(ratings)
    cover = race.cover_viability(rating_map, race.FORM_TABLE, "Pegasus", COVER_BOOST, COVER_SIGMA)
    return {
        "horses": len(ratings),
        "records": len(race.FORM_TABLE),
        "ratings": dict(rating_map),
        "win_probabilities": probs,
        "pegasus_win_delta": cover["win_delta"],
        "detection_risk": cover["detection_risk"],
        "expected_value": cover["expected_value"],
    }


def acquisition_metrics() -> dict[str, Any]:
    """Computed monopoly-acquisition optimization metrics."""
    chain = chip.build_default_supply_chain()
    improved = acq.improvement(chain, ACQUISITION_BUDGET, "hhi")
    _, optimal_score = acq.optimal_acquisition(chain, ACQUISITION_BUDGET, "hhi")
    _, greedy_score = acq.greedy_acquisition(chain, ACQUISITION_BUDGET, "hhi")
    return {
        "budget": ACQUISITION_BUDGET,
        "acquireable": list(acq.acquireable_firms(chain)),
        "optimal_acquired": list(improved.acquired),
        "optimal_hhi": improved.score,
        "baseline_hhi": improved.baseline,
        "hhi_gain": improved.gain,
        "greedy_hhi": greedy_score,
        "regret": float(optimal_score - greedy_score),
    }


def valley_metrics() -> dict[str, Any]:
    """Computed valley-impact (urban sabotage) coupling metrics."""
    mine = flood.build_default_mine()
    sim = flood.simulate_flood(mine, ("adit",), FLOOD_PARAMS)
    fabs = valley.build_default_valley()
    report = valley.valley_report(mine, sim, fabs, FLOOD_PARAMS.horizon)
    return {
        "fabs": len(fabs),
        "capacity_loss": report["capacity_loss"],
        "inoperable": report["inoperable"],
        "victims": report["victims"],
        "survivors": report["survivors"],
    }


def market_metrics() -> dict[str, Any]:
    """Computed racing betting-market / cover-finance metrics."""
    ratings = race.form_ratings(race.FORM_TABLE)
    probs = {name: hr.rating for name, hr in ratings.items()}
    plan = mkt.cover_bankroll(probs, "Pegasus", COVER_BOOST, COVER_BANKROLL)
    return {
        "horse": plan.horse,
        "true_probability": plan.true_probability,
        "market_implied_probability": plan.market_implied_probability,
        "value_edge": plan.value_edge,
        "kelly_fraction": plan.kelly_fraction,
        "kelly_stake": plan.kelly_stake,
        "expected_profit": plan.expected_profit,
    }


def run_mission_metrics() -> dict[str, Any]:
    """Aggregate the six concept metric groups into one deterministic map.

    This is the canonical result payload the ``execute`` stage reports, kept
    separate from the provider so tests, figures, and the manuscript pipeline
    can call it directly without driving a mission — and without needing
    ``bond_api`` to be installed.
    """
    return {
        "chip": chip_metrics(),
        "flood": flood_metrics(),
        "race": race_metrics(),
        "acquisition": acquisition_metrics(),
        "valley": valley_metrics(),
        "market": market_metrics(),
    }
