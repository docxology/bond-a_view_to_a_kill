"""ZORIN — the *A View to a Kill* (1985) mission provider for BOND-API.

This module is the thin adapter between the film's pure domain core (the six
concept modules, aggregated by :mod:`a_view_to_a_kill.metrics`) and the FROZEN
:class:`bond_api.protocol.MissionProvider` contract. It is the only module in
this package that imports ``bond_api`` — everything else, including the
manuscript pipeline and the figure renderers, depends on ``metrics`` instead,
so the pure core genuinely stays importable when the ``bond-api`` path
dependency is unavailable (pinned by ``tests/test_bond_api_fallback.py``).

Public surface — FROZEN, consumed by bond-cli, the coordinator reconcile, and
the orchestrator; do not rename or re-shape:

* ``MissionProvider`` — ``brief`` / ``recon`` / ``plan`` / ``execute`` /
  ``debrief``, discovered by the slug ``a_view_to_a_kill``.
* ``gadget_registry`` — a module-level :class:`bond_api.registry.GadgetRegistry`
  carrying six zero-argument metric gadgets, so the orchestrator can pull
  computed mission metrics without re-running the stages.
* ``run_mission_metrics`` and the scenario constants (``SEED``,
  ``FLOOD_PARAMS``, ``ACQUIRED_FIRMS``, ``COVER_BOOST``, ``COVER_SIGMA``,
  ``ACQUISITION_BUDGET``, ``COVER_BANKROLL``, ``PACKAGE_VERSION``), re-exported
  from :mod:`a_view_to_a_kill.metrics` so existing importers keep working.
"""

from __future__ import annotations

import hashlib
import json

from a_view_to_a_kill.metrics import (
    ACQUIRED_FIRMS,
    ACQUISITION_BUDGET,
    COVER_BANKROLL,
    COVER_BOOST,
    COVER_SIGMA,
    FLOOD_PARAMS,
    PACKAGE_VERSION,
    SEED,
    acquisition_metrics,
    chip_metrics,
    flood_metrics,
    market_metrics,
    race_metrics,
    run_mission_metrics,
    valley_metrics,
)
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

__all__ = [
    "MissionProvider",
    "gadget_registry",
    "run_mission_metrics",
    "chip_metrics",
    "flood_metrics",
    "race_metrics",
    "acquisition_metrics",
    "valley_metrics",
    "market_metrics",
    "PACKAGE_VERSION",
    "SEED",
    "FLOOD_PARAMS",
    "ACQUIRED_FIRMS",
    "COVER_BOOST",
    "COVER_SIGMA",
    "ACQUISITION_BUDGET",
    "COVER_BANKROLL",
]

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
        """Declare the ZORIN mission: six objectives over the three film pieces.

        Asset payloads are *measured* from the pure core rather than written as
        literals, so a change to a default dataset cannot leave the brief
        quietly describing a market, mine, or race card that no longer exists.
        """
        chip_m = chip_metrics()
        flood_m = flood_metrics()
        race_m = race_metrics()
        return MissionBrief(
            film=self.film,
            codename="ZORIN",
            objectives=(
                "map microchip supply-chain monopoly choke points",
                "optimize the budgeted acquisition that corners the market",
                "model flood-the-mine water-ingress dynamics",
                "couple the flood to surface-fab capacity loss in the valley",
                "score horse-race form analytics for the cover operation",
                "price the cover's betting-market position and staking",
            ),
            assets=(
                Asset(
                    kind="dataset",
                    name="supply_chain",
                    payload={"nodes": chip_m["nodes"], "links": chip_m["links"]},
                ),
                Asset(
                    kind="network",
                    name="main_strike",
                    payload={"chambers": flood_m["chambers"], "tunnels": flood_m["tunnels"]},
                ),
                Asset(
                    kind="form",
                    name="race_card",
                    payload={"horses": race_m["horses"], "records": race_m["records"]},
                ),
            ),
            constraints=(
                Constraint(kind="determinism", detail="no random draws, no wall-clock dependence"),
                Constraint(kind="no-mocks", detail="real computation and real data only"),
                Constraint(kind="scope", detail="microchip supply chain, mine flooding, race cover"),
            ),
        )

    def recon(self, request: ReconRequest) -> ReconReport:
        """Survey the request, the three datasets, and the determinism constraint.

        Like :meth:`brief`, every quantity in a finding is measured from the
        pure core at call time — no hand-written counts that could drift.
        """
        chip_m = chip_metrics()
        flood_m = flood_metrics()
        race_m = race_metrics()
        races_each = race_m["records"] // race_m["horses"]
        return ReconReport(
            findings=(
                Finding(label="goal", detail=request.goal),
                Finding(
                    label="supply_chain",
                    detail=(
                        f"documented 1985 microchip market graph: {chip_m['nodes']} firms, "
                        f"{chip_m['links']} supply links"
                    ),
                ),
                Finding(
                    label="mine",
                    detail=(
                        f"Main Strike network: {flood_m['chambers']} chambers, "
                        f"{flood_m['tunnels']} tunnels, {flood_m['total_volume']:.0f} m^3 total volume"
                    ),
                ),
                Finding(
                    label="race_card",
                    detail=(
                        f"Epsom-style form card: {race_m['horses']} horses, {races_each} races each "
                        f"({race_m['records']} records)"
                    ),
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
