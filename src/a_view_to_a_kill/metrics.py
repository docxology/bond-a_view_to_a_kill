"""ZORIN mission scenario parameters and computed metric groups (pure).

This module holds everything the mission *computes* — the mission scenario
(:class:`MissionScenario`) and the six deterministic metric groups — with
**no** ``bond_api`` import. :mod:`a_view_to_a_kill.mission` re-exports every
public name here and adds only the protocol adapter (``MissionProvider``) and
the gadget registry.

The split exists so the documented fallback is actually true: the pure core,
:mod:`a_view_to_a_kill.manuscript_variables`, and
:mod:`a_view_to_a_kill.figures` can all run when the ``bond-api`` path
dependency is unavailable. Before the split they imported ``mission``, which
imports ``bond_api.protocol`` at module level, so the fallback silently did
not hold — ``tests/test_bond_api_fallback.py`` now pins it.

**Every metric group is a function of a :class:`MissionScenario`.** The knobs
in ``manuscript/config.yaml`` are turned into a scenario by
:func:`scenario_from_config` and threaded all the way down into the pure
models, so changing a knob changes the computed numbers — not just the
``CONFIG_*`` tokens that echo the file back. :data:`DEFAULT_SCENARIO` is the
module-level default and is pinned equal to the config file by
``tests/test_metrics_scenario.py``; the same test proves each knob moves a
computed metric, so an inert knob fails the suite.

Nothing here does I/O, draws randomness, or reads the wall clock: two calls to
:func:`run_mission_metrics` with the same scenario return equal payloads.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from a_view_to_a_kill import acquisition as acq
from a_view_to_a_kill import chip_supply_chain as chip
from a_view_to_a_kill import mine_flood as flood
from a_view_to_a_kill import race_analytics as race
from a_view_to_a_kill import race_market as mkt
from a_view_to_a_kill import valley_impact as valley

__all__ = [
    "PACKAGE_VERSION",
    "SEED",
    "MissionScenario",
    "DEFAULT_SCENARIO",
    "SCENARIO_CONFIG_KEYS",
    "scenario_from_config",
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

#: Euler timestep (s) for the flood integrator. A *structural* model constant,
#: not a scenario knob: it belongs to the numerical scheme, so it lives in the
#: code and is surfaced to the manuscript as a ``CORE_*`` token.
FLOOD_DT = 1.0


@dataclass(frozen=True)
class MissionScenario:
    """The tunable ZORIN scenario — the knobs ``manuscript/config.yaml`` owns.

    Every field is consumed by at least one metric group (proved by
    ``tests/test_metrics_scenario.py::test_every_scenario_knob_moves_a_metric``).
    Structural model constants (discharge coefficient, detection threshold,
    par pace, purse, penalty, Euler timestep) are deliberately *not* here:
    they belong to the models and live in the pure modules.
    """

    flood_ingress_rate: float
    flood_horizon: float
    race_halflife: float
    cover_boost: float
    cover_sigma: float
    acquisition_budget: int
    cover_bankroll: float
    market_overround: float
    acquired_firms: tuple[str, ...]

    def __post_init__(self) -> None:
        for label in ("flood_ingress_rate", "flood_horizon", "race_halflife", "cover_sigma"):
            value = getattr(self, label)
            if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
                raise ValueError(f"MissionScenario.{label} must be a positive number")
        if not isinstance(self.cover_boost, (int, float)) or isinstance(self.cover_boost, bool):
            raise ValueError("MissionScenario.cover_boost must be a number")
        if self.cover_boost < 0:
            raise ValueError("MissionScenario.cover_boost must be non-negative")
        if not isinstance(self.acquisition_budget, int) or isinstance(self.acquisition_budget, bool):
            raise ValueError("MissionScenario.acquisition_budget must be an integer")
        if self.acquisition_budget < 0:
            raise ValueError("MissionScenario.acquisition_budget must be non-negative")
        if not isinstance(self.cover_bankroll, (int, float)) or isinstance(self.cover_bankroll, bool):
            raise ValueError("MissionScenario.cover_bankroll must be a number")
        if self.cover_bankroll <= 0:
            raise ValueError("MissionScenario.cover_bankroll must be positive")
        if not isinstance(self.market_overround, (int, float)) or isinstance(self.market_overround, bool):
            raise ValueError("MissionScenario.market_overround must be a number")
        if self.market_overround <= 1.0:
            raise ValueError("MissionScenario.market_overround must be strictly greater than 1.0")
        if not isinstance(self.acquired_firms, tuple) or not self.acquired_firms:
            raise ValueError("MissionScenario.acquired_firms must be a non-empty tuple")
        if any(not isinstance(name, str) or not name.strip() for name in self.acquired_firms):
            raise ValueError("MissionScenario.acquired_firms entries must be non-empty strings")

    @property
    def flood_params(self) -> flood.FloodParams:
        """The flood integrator parameters implied by this scenario."""
        return flood.FloodParams(
            ingress_rate=float(self.flood_ingress_rate),
            horizon=float(self.flood_horizon),
            dt=FLOOD_DT,
        )


#: The ``experiment:`` keys :func:`scenario_from_config` requires. Missing keys
#: are an error rather than a silent fall back to a hard-coded default — a
#: silent default is exactly how a config knob becomes inert.
SCENARIO_CONFIG_KEYS = (
    "flood_ingress_rate",
    "flood_horizon",
    "race_halflife",
    "cover_boost",
    "cover_sigma",
    "acquisition_budget",
    "cover_bankroll",
    "market_overround",
    "scenario_acquired_firms",
)


def scenario_from_config(experiment: Mapping[str, Any]) -> MissionScenario:
    """Build a :class:`MissionScenario` from a config ``experiment:`` mapping.

    Raises ``ValueError`` if any key in :data:`SCENARIO_CONFIG_KEYS` is absent,
    so a renamed or dropped knob fails loudly instead of quietly reverting to
    a module default.
    """
    missing = [key for key in SCENARIO_CONFIG_KEYS if key not in experiment]
    if missing:
        raise ValueError(f"manuscript config 'experiment' section is missing keys: {missing}")
    acquired = experiment["scenario_acquired_firms"]
    if isinstance(acquired, str) or not isinstance(acquired, (list, tuple)):
        raise ValueError("experiment.scenario_acquired_firms must be a list of firm names")
    return MissionScenario(
        flood_ingress_rate=float(experiment["flood_ingress_rate"]),
        flood_horizon=float(experiment["flood_horizon"]),
        race_halflife=float(experiment["race_halflife"]),
        cover_boost=float(experiment["cover_boost"]),
        cover_sigma=float(experiment["cover_sigma"]),
        acquisition_budget=int(experiment["acquisition_budget"]),
        cover_bankroll=float(experiment["cover_bankroll"]),
        market_overround=float(experiment["market_overround"]),
        acquired_firms=tuple(str(name) for name in acquired),
    )


#: The scenario used when a caller supplies none. Pinned equal to
#: ``manuscript/config.yaml`` by ``tests/test_metrics_scenario.py``.
DEFAULT_SCENARIO = MissionScenario(
    flood_ingress_rate=10.0,
    flood_horizon=900.0,
    race_halflife=2.0,
    cover_boost=0.2,
    cover_sigma=0.5,
    acquisition_budget=2,
    cover_bankroll=100_000.0,
    market_overround=1.12,
    acquired_firms=("amd_fab", "nec_fab"),
)

#: Backwards-compatible aliases for the default scenario's knobs. ``mission``
#: re-exports these; they are views on :data:`DEFAULT_SCENARIO`, never a second
#: source of truth.
FLOOD_PARAMS = DEFAULT_SCENARIO.flood_params
ACQUIRED_FIRMS = DEFAULT_SCENARIO.acquired_firms
COVER_BOOST = DEFAULT_SCENARIO.cover_boost
COVER_SIGMA = DEFAULT_SCENARIO.cover_sigma
ACQUISITION_BUDGET = DEFAULT_SCENARIO.acquisition_budget
COVER_BANKROLL = DEFAULT_SCENARIO.cover_bankroll

#: The metric-group keys :func:`run_mission_metrics` always populates.
METRIC_GROUPS = ("chip", "flood", "race", "acquisition", "valley", "market")


def _zorin_owned_firms(chain: chip.SupplyChain) -> set[str]:
    """Names of firms ZORIN already owns before any acquisition."""
    return {supplier.name for supplier in chain.suppliers if supplier.owner == "zorin"}


def chip_metrics(scenario: MissionScenario = DEFAULT_SCENARIO) -> dict[str, Any]:
    """Computed supply-chain security metrics for the ZORIN monopoly attack."""
    chain = chip.build_default_supply_chain()
    acquired = list(scenario.acquired_firms)
    retained_fabs = sorted(
        supplier.name
        for supplier in chain.suppliers
        if supplier.stage == "fabrication" and supplier.name not in set(acquired)
    )
    return {
        "nodes": len(chain.suppliers),
        "links": len(chain.links),
        "hhi_before": chip.hhi(chain),
        "hhi_after": chip.post_elimination_hhi(chain, tuple(acquired)),
        "zorin_fab_share": chip.monopoly_share(chain, tuple(acquired))["fabrication"],
        "top_choke_points": chip.top_choke_points(chain, 3),
        "scenario_acquired": acquired,
        # The cascade removes exactly the acquired-and-dismantled firms; these
        # are the fabricators that survive that removal and keep supplying the
        # assembly stage.
        "cascade_removed": acquired,
        "cascade_retained_fabs": retained_fabs,
        "cascade_starved_firms": sorted(chip.cascade_starved(chain, acquired)[0]),
        "cascade_starved_fraction": chip.cascade_starved(chain, acquired)[1],
    }


def flood_metrics(scenario: MissionScenario = DEFAULT_SCENARIO) -> dict[str, Any]:
    """Computed mine-flood water-ingress metrics for the ZORIN sabotage."""
    params = scenario.flood_params
    mine = flood.build_default_mine()
    sim = flood.simulate_flood(mine, ("adit",), params)
    return {
        "chambers": len(mine.chambers),
        "tunnels": len(mine.tunnels),
        "total_volume": float(sum(c.volume for c in mine.chambers)),
        "flooded_fraction": flood.flooded_fraction(sim, params.horizon),
        "vault_flood_time": flood.flooded_at(sim, "vault"),
        "critical_ingress": flood.critical_ingress(mine, ("adit", "shaft_a", "shaft_b"), params),
        "water_balance_error": flood.water_balance_error(sim),
    }


def race_metrics(scenario: MissionScenario = DEFAULT_SCENARIO) -> dict[str, Any]:
    """Computed race-form analytics and cover-operation risk metrics."""
    ratings = race.form_ratings(race.FORM_TABLE, halflife=scenario.race_halflife)
    rating_map = {name: hr.rating for name, hr in ratings.items()}
    probs = race.win_probabilities(ratings)
    cover = race.cover_viability(
        rating_map,
        race.FORM_TABLE,
        "Pegasus",
        scenario.cover_boost,
        scenario.cover_sigma,
    )
    return {
        "horses": len(ratings),
        "records": len(race.FORM_TABLE),
        "ratings": dict(rating_map),
        "win_probabilities": probs,
        "pegasus_win_delta": cover["win_delta"],
        "detection_risk": cover["detection_risk"],
        "expected_value": cover["expected_value"],
    }


def acquisition_metrics(scenario: MissionScenario = DEFAULT_SCENARIO) -> dict[str, Any]:
    """Computed monopoly-acquisition optimization metrics.

    Also scores the *scenario* acquisition (the film-faithful set ZORIN buys)
    on the same objective, so the manuscript can state how far the scenario
    falls short of the optimizer's answer instead of leaving the two numbers
    side by side and unreconciled.
    """
    chain = chip.build_default_supply_chain()
    improved = acq.improvement(chain, scenario.acquisition_budget, "hhi")
    _, optimal_score = acq.optimal_acquisition(chain, scenario.acquisition_budget, "hhi")
    _, greedy_score = acq.greedy_acquisition(chain, scenario.acquisition_budget, "hhi")
    scenario_acquired = tuple(scenario.acquired_firms)
    scenario_hhi = chip.post_elimination_hhi(chain, scenario_acquired)
    return {
        "budget": scenario.acquisition_budget,
        "acquireable": list(acq.acquireable_firms(chain)),
        "optimal_acquired": list(improved.acquired),
        "optimal_hhi": improved.score,
        "optimal_fab_share": chip.monopoly_share(chain, tuple(improved.acquired))["fabrication"],
        "baseline_hhi": improved.baseline,
        "hhi_gain": improved.gain,
        "greedy_hhi": greedy_score,
        "regret": float(optimal_score - greedy_score),
        "scenario_acquired": list(scenario_acquired),
        "scenario_size": len(scenario_acquired),
        "scenario_hhi": float(scenario_hhi),
        "scenario_fab_share": chip.monopoly_share(chain, scenario_acquired)["fabrication"],
        "scenario_shortfall": float(improved.score - scenario_hhi),
    }


def valley_metrics(scenario: MissionScenario = DEFAULT_SCENARIO) -> dict[str, Any]:
    """Computed valley-impact (urban sabotage) coupling metrics.

    Splits victims and survivors by ownership so the manuscript's claim about
    *who* the flood spares is a computed set operation rather than prose.
    """
    params = scenario.flood_params
    mine = flood.build_default_mine()
    sim = flood.simulate_flood(mine, ("adit",), params)
    fabs = valley.build_default_valley()
    report = valley.valley_report(mine, sim, fabs, params.horizon)
    acquired = set(scenario.acquired_firms)
    zorin_owned = _zorin_owned_firms(chip.build_default_supply_chain())
    victims = list(report["victims"])
    survivors = list(report["survivors"])
    return {
        "fabs": len(fabs),
        "capacity_loss": report["capacity_loss"],
        "inoperable": report["inoperable"],
        "victims": victims,
        "survivors": survivors,
        # ownership split — ZORIN-controlled means owned outright or acquired
        "acquired_victims": sorted(set(victims) & acquired),
        "acquired_survivors": sorted(set(survivors) & acquired),
        "unacquired_survivors": sorted(set(survivors) - acquired - zorin_owned),
        "unacquired_victims": sorted(set(victims) - acquired - zorin_owned),
    }


def market_metrics(scenario: MissionScenario = DEFAULT_SCENARIO) -> dict[str, Any]:
    """Computed racing betting-market / cover-finance metrics.

    Passes the EWMA *form ratings* (which is what
    :func:`a_view_to_a_kill.race_market.cover_bankroll` documents itself as
    taking); the honest book is built from the softmax win probabilities
    derived from those ratings, so the market-implied probability and the
    boosted true probability come from the same probability model.
    """
    ratings = race.form_ratings(race.FORM_TABLE, halflife=scenario.race_halflife)
    rating_map = {name: hr.rating for name, hr in ratings.items()}
    plan = mkt.cover_bankroll(
        rating_map,
        "Pegasus",
        scenario.cover_boost,
        scenario.cover_bankroll,
        overround=scenario.market_overround,
    )
    return {
        "horse": plan.horse,
        "true_probability": plan.true_probability,
        "market_implied_probability": plan.market_implied_probability,
        "value_edge": plan.value_edge,
        "kelly_fraction": plan.kelly_fraction,
        "kelly_stake": plan.kelly_stake,
        "expected_profit": plan.expected_profit,
    }


def run_mission_metrics(scenario: MissionScenario = DEFAULT_SCENARIO) -> dict[str, Any]:
    """Aggregate the six concept metric groups into one deterministic map.

    This is the canonical result payload the ``execute`` stage reports, kept
    separate from the provider so tests, figures, and the manuscript pipeline
    can call it directly without driving a mission — and without needing
    ``bond_api`` to be installed.
    """
    return {
        "chip": chip_metrics(scenario),
        "flood": flood_metrics(scenario),
        "race": race_metrics(scenario),
        "acquisition": acquisition_metrics(scenario),
        "valley": valley_metrics(scenario),
        "market": market_metrics(scenario),
    }
