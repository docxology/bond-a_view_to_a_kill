"""Tests for the ZORIN mission provider adapter (mission.py) + BOND-API wiring."""

from __future__ import annotations

import json

import pytest
from bond_api.protocol import (
    MissionProvider as ProtocolMissionProvider,
    ReconRequest,
    run_mission,
)

from a_view_to_a_kill import chip_supply_chain as chip
from a_view_to_a_kill import mine_flood as flood
from a_view_to_a_kill import race_analytics as race
from a_view_to_a_kill.mission import (
    ACQUIRED_FIRMS,
    COVER_BOOST,
    MissionProvider,
    PACKAGE_VERSION,
    SEED,
    gadget_registry,
)


def test_provider_satisfies_protocol() -> None:
    provider = MissionProvider()
    assert isinstance(provider, ProtocolMissionProvider)
    assert provider.film == "a_view_to_a_kill"


def test_brief_declares_zorin_mission() -> None:
    brief = MissionProvider().brief()
    assert brief.codename == "ZORIN"
    assert brief.film == "a_view_to_a_kill"
    assert len(brief.objectives) == 3
    assert len(brief.assets) == 3
    assert any(c.kind == "determinism" for c in brief.constraints)


def test_full_mission_flow_is_deterministic() -> None:
    provider = MissionProvider()
    a = run_mission(provider, ReconRequest("run"))
    b = run_mission(provider, ReconRequest("run"))
    assert json.dumps(a.outcome.results, sort_keys=True) == json.dumps(b.outcome.results, sort_keys=True)
    assert a.outcome.success is True
    assert a.outcome.provenance.seed == SEED
    assert a.outcome.provenance.package_version == PACKAGE_VERSION
    assert a.outcome.provenance.wall_time_s == 0.0
    assert len(a.outcome.provenance.input_hash) == 64


def test_execute_reports_all_concept_groups() -> None:
    provider = MissionProvider()
    outcome = provider.execute(provider.plan(provider.brief()))
    assert set(outcome.results) >= {
        "chip",
        "flood",
        "race",
        "acquisition",
        "valley",
        "market",
        "steps_completed",
    }
    assert "top_choke_points" in outcome.results["chip"]
    assert "flooded_fraction" in outcome.results["flood"]
    assert "detection_risk" in outcome.results["race"]
    assert "optimal_hhi" in outcome.results["acquisition"]
    assert "capacity_loss" in outcome.results["valley"]
    assert "kelly_stake" in outcome.results["market"]


def test_debrief_has_lessons() -> None:
    provider = MissionProvider()
    debrief = run_mission(provider, ReconRequest("run"))
    assert len(debrief.lessons) >= 1


def test_mission_metrics_match_pure_core_directly() -> None:
    """The mission-reported metrics must equal the pure-core computations."""
    provider = MissionProvider()
    outcome = provider.execute(provider.plan(provider.brief()))
    chain = chip.build_default_supply_chain()
    assert outcome.results["chip"]["hhi_before"] == pytest.approx(chip.hhi(chain))
    assert outcome.results["chip"]["hhi_after"] == pytest.approx(chip.post_elimination_hhi(chain, ACQUIRED_FIRMS))
    sim = flood.simulate_flood(flood.build_default_mine(), ("adit",), flood.FloodParams(10.0, 900.0))
    assert outcome.results["flood"]["flooded_fraction"] == pytest.approx(flood.flooded_fraction(sim, 900.0))
    ratings = race.form_ratings(race.FORM_TABLE)
    monkey = {name: hr.rating for name, hr in ratings.items()}
    cover = race.cover_viability(monkey, race.FORM_TABLE, "Pegasus", COVER_BOOST, 0.5)
    assert outcome.results["race"]["expected_value"] == pytest.approx(cover["expected_value"])


def test_gadgets_registered_and_callable() -> None:
    assert "a_view_to_a_kill" in gadget_registry
    assert gadget_registry.gadgets_for("a_view_to_a_kill") == (
        "chip_metrics",
        "flood_metrics",
        "race_metrics",
        "acquisition_metrics",
        "valley_metrics",
        "market_metrics",
    )
    assert "hhi_before" in gadget_registry.lookup("a_view_to_a_kill", "chip_metrics")()
    assert "water_balance_error" in gadget_registry.lookup("a_view_to_a_kill", "flood_metrics")()
    assert "detection_risk" in gadget_registry.lookup("a_view_to_a_kill", "race_metrics")()
    assert "optimal_hhi" in gadget_registry.lookup("a_view_to_a_kill", "acquisition_metrics")()
    assert "capacity_loss" in gadget_registry.lookup("a_view_to_a_kill", "valley_metrics")()
    assert "kelly_stake" in gadget_registry.lookup("a_view_to_a_kill", "market_metrics")()


def test_gadgets_are_deterministic() -> None:
    lookup = gadget_registry.lookup
    a = json.dumps(lookup("a_view_to_a_kill", "chip_metrics")(), sort_keys=True)
    b = json.dumps(lookup("a_view_to_a_kill", "chip_metrics")(), sort_keys=True)
    assert a == b


def test_flood_water_balance_is_machine_precise_in_mission() -> None:
    provider = MissionProvider()
    outcome = provider.execute(provider.plan(provider.brief()))
    assert outcome.results["flood"]["water_balance_error"] < 1e-9
