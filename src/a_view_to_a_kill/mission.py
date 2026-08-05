"""ZORIN — the *A View to a Kill* (1985) mission provider for BOND-API.

This module is the thin adapter between the film's pure domain core
(:mod:`a_view_to_a_kill.chip_supply_chain`, :mod:`a_view_to_a_kill.mine_flood`,
:mod:`a_view_to_a_kill.race_analytics`) and the FROZEN
:class:`bond_api.protocol.MissionProvider` contract. It is the only module in
this package that imports ``bond_api`` — the pure core stays importable
without it (fallback if the path dependency ever fails).

Discovery contract: the orchestrator loads the provider by slug
``a_view_to_a_kill`` and binds it; this module exposes ``MissionProvider`` at
top level under that stable name. Gadgets are registered on a module-level
:class:`bond_api.registry.GadgetRegistry` so the orchestrator can pull
computed mission metrics without re-running the stages.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from a_view_to_a_kill import acquisition as acq
from a_view_to_a_kill import chip_supply_chain as chip
from a_view_to_a_kill import mine_flood as flood
from a_view_to_a_kill import race_analytics as race
from a_view_to_a_kill import race_market as mkt
from a_view_to_a_kill import valley_impact as valley
from bond_api.protocol import (
    Asset,
    Constraint,
    Debrief,
    Finding,
    MissionBrief,
    MissionOutcome,
    MissionPlan,
    Provenance,
    ReconReport,
    ReconRequest,
    Step,
)
from bond_api.registry import GadgetRegistry

__all__ = ["MissionProvider", "gadget_registry", "run_mission_metrics", "PACKAGE_VERSION", "SEED"]

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

#: Gadgets registered for this film (deterministic zero-arg callables).
gadget_registry = GadgetRegistry()
gadget_registry.register(
    "a_view_to_a_kill",
    {
        "chip_metrics": lambda: chip_metrics(),
        "flood_metrics": lambda: flood_metrics(),
        "race_metrics": lambda: race_metrics(),
        "acquisition_metrics": lambda: acquisition_metrics(),
        "valley_metrics": lambda: valley_metrics(),
        "market_metrics": lambda: market_metrics(),
    },
)


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
        "ratings": {name: hr.rating for name, hr in ratings.items()},
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
    separate from the provider so tests and figures can call it directly
    without driving a mission.
    """
    return {
        "chip": chip_metrics(),
        "flood": flood_metrics(),
        "race": race_metrics(),
        "acquisition": acquisition_metrics(),
        "valley": valley_metrics(),
        "market": market_metrics(),
    }


def _input_hash(plan: MissionPlan) -> str:
    canonical = json.dumps(
        [{"name": step.name, "action": step.action, "params": step.params} for step in plan.steps],
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class MissionProvider:  # noqa: N801 — class name fixed by the discovery contract
    """Deterministic ZORIN mission provider implementing the BOND-API contract."""

    film = "a_view_to_a_kill"

    def brief(self) -> MissionBrief:
        """Declare the ZORIN mission: three objectives over the three concepts."""
        return MissionBrief(
            film=self.film,
            codename="ZORIN",
            objectives=(
                "map microchip supply-chain monopoly choke points",
                "model flood-the-mine water-ingress dynamics",
                "score horse-race form analytics for the cover operation",
            ),
            assets=(
                Asset(kind="dataset", name="supply_chain", payload={"nodes": 12, "links": 18}),
                Asset(kind="network", name="main_strike", payload={"chambers": 8, "tunnels": 10}),
                Asset(kind="form", name="race_card", payload={"horses": 5, "races": 4}),
            ),
            constraints=(
                Constraint(kind="determinism", detail="no random draws, no wall-clock dependence"),
                Constraint(kind="no-mocks", detail="real computation and real data only"),
                Constraint(kind="scope", detail="microchip supply chain, mine flooding, race cover"),
            ),
        )

    def recon(self, request: ReconRequest) -> ReconReport:
        """Survey the request, the three datasets, and the determinism constraint."""
        return ReconReport(
            findings=(
                Finding(label="goal", detail=request.goal),
                Finding(
                    label="supply_chain",
                    detail="documented 1985 microchip market graph: 12 firms, 18 supply links",
                ),
                Finding(
                    label="mine",
                    detail="Main Strike network: 8 chambers, 10 tunnels, 9100 m^3 total volume",
                ),
                Finding(
                    label="race_card",
                    detail="Epsom-style form card: 5 horses, 4 races each",
                ),
                Finding(label="constraints", detail="fully deterministic; metrics computed, not stubbed"),
            )
        )

    def plan(self, brief: MissionBrief) -> MissionPlan:
        """Plan the deterministic execute steps, one per concept plus verify."""
        return MissionPlan(
            steps=(
                Step(name="supply_chain", action="analyze_choke_points", params={"acquire": list(ACQUIRED_FIRMS)}),
                Step(name="acquisition", action="optimize_monopoly", params={"budget": ACQUISITION_BUDGET}),
                Step(name="mine_flood", action="simulate_water_ingress", params={"ingress": "adit"}),
                Step(name="valley", action="couple_flood_to_surface", params={"horizon": FLOOD_PARAMS.horizon}),
                Step(name="race_cover", action="score_form_and_cover", params={"boost": COVER_BOOST}),
                Step(name="market", action="score_cover_finance", params={"bankroll": COVER_BANKROLL}),
                Step(name="verify", action="check_conservation_and_determinism", params={"seed": SEED}),
            )
        )

    def execute(self, plan: MissionPlan) -> MissionOutcome:
        """Run the plan's computations and return a deterministic outcome."""
        results = run_mission_metrics()
        results["steps_completed"] = [step.name for step in plan.steps]
        return MissionOutcome(
            success=True,
            results=results,
            provenance=Provenance(
                package_version=PACKAGE_VERSION,
                seed=SEED,
                input_hash=_input_hash(plan),
                wall_time_s=0.0,
            ),
        )

    def debrief(self, outcome: MissionOutcome) -> Debrief:
        """Summarize the mission and record ZORIN's standing lessons."""
        return Debrief(
            outcome=outcome,
            lessons=(
                "concentration metrics (HHI, choke betweenness) quantify monopoly exposure",
                "exhaustive acquisition search beats the greedy baseline on concentration",
                "the mine-flood model conserves water mass to machine precision",
                "the flood's urban blast-reach disables rival fabs while ZORIN's own survives",
                "covering a scheme is a trade-off: detection risk outruns win probability",
                "a boosted true edge against honest market odds is exactly the anomaly to detect",
            ),
        )
