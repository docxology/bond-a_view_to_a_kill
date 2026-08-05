"""The config knobs must actually drive the computation.

This module exists because of a specific defect: `manuscript/config.yaml`
declared an `experiment:` block that the manuscript described as prescribing
every result, while `metrics.py` hard-coded its own copies of the same
numbers. Rewriting every knob in the file changed all the `CONFIG_*` tokens
and **zero** computed tokens — the knobs were reported but never consumed.

The gates below are written so that regression fails loudly:

* :func:`test_default_scenario_matches_the_config_file` pins the code default
  to the file, so they cannot drift into two answers.
* :func:`test_every_scenario_knob_moves_a_metric` perturbs each knob one at a
  time and requires the computed payload to change. Reverting any knob to a
  module constant makes exactly that parametrization go red.
* :func:`test_config_edit_moves_computed_manuscript_tokens` runs the original
  falsifying experiment end to end: write a modified config, hydrate the
  manuscript variables from it, and require the *computed* tokens (not just
  the `CONFIG_*` echoes) to move.

No mocks: every assertion runs the real models on real config files.
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import pytest
import yaml

from a_view_to_a_kill import chip_supply_chain as chip
from a_view_to_a_kill import manuscript_variables as msv
from a_view_to_a_kill import metrics

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PACKAGE_ROOT / "manuscript" / "config.yaml"


def _config() -> dict[str, Any]:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))


# --------------------------------------------------------------- config <-> code
def test_config_has_every_scenario_key() -> None:
    experiment = _config()["experiment"]
    missing = [key for key in metrics.SCENARIO_CONFIG_KEYS if key not in experiment]
    assert not missing, f"config.yaml experiment section is missing {missing}"


def test_default_scenario_matches_the_config_file() -> None:
    """`DEFAULT_SCENARIO` is a view on the config, not a second source of truth."""
    from_file = metrics.scenario_from_config(_config()["experiment"])
    assert from_file == metrics.DEFAULT_SCENARIO


def test_legacy_constants_are_views_on_the_default_scenario() -> None:
    """The re-exported names `mission` publishes stay tied to the scenario."""
    scenario = metrics.DEFAULT_SCENARIO
    assert metrics.ACQUIRED_FIRMS == scenario.acquired_firms
    assert metrics.COVER_BOOST == scenario.cover_boost
    assert metrics.COVER_SIGMA == scenario.cover_sigma
    assert metrics.ACQUISITION_BUDGET == scenario.acquisition_budget
    assert metrics.COVER_BANKROLL == scenario.cover_bankroll
    assert metrics.FLOOD_PARAMS == scenario.flood_params


@pytest.mark.parametrize("key", metrics.SCENARIO_CONFIG_KEYS)
def test_scenario_from_config_requires_every_key(key: str) -> None:
    """A dropped or renamed knob is an error, never a silent module default."""
    experiment = dict(_config()["experiment"])
    experiment.pop(key)
    with pytest.raises(ValueError, match="missing keys"):
        metrics.scenario_from_config(experiment)


def test_scenario_from_config_rejects_scalar_acquisition_set() -> None:
    experiment = dict(_config()["experiment"])
    experiment["scenario_acquired_firms"] = "amd_fab"
    with pytest.raises(ValueError, match="must be a list"):
        metrics.scenario_from_config(experiment)


# --------------------------------------------------------------- knob liveness
#: One perturbation per knob, each chosen to be a genuinely different scenario,
#: paired with **every** metric group that must respond to it. Naming the
#: groups matters: a knob consumed by only one of its two consumers still
#: changes the aggregate payload, so an aggregate-only assertion would let a
#: half-wired knob through.
KNOB_PERTURBATIONS: tuple[tuple[str, Any, tuple[str, ...]], ...] = (
    ("flood_ingress_rate", 3.0, ("flood", "valley")),
    ("flood_horizon", 200.0, ("flood", "valley")),
    ("race_halflife", 0.5, ("race", "market")),
    ("cover_boost", 0.9, ("race", "market")),
    ("cover_sigma", 0.15, ("race",)),
    ("acquisition_budget", 1, ("acquisition",)),
    ("cover_bankroll", 25_000.0, ("market",)),
    ("market_overround", 1.45, ("market",)),
    ("acquired_firms", ("intel_fab", "nec_fab"), ("chip", "acquisition", "valley")),
)


def _perturbed(knob: str, value: Any) -> metrics.MissionScenario:
    base = metrics.DEFAULT_SCENARIO
    fields = {
        "flood_ingress_rate": base.flood_ingress_rate,
        "flood_horizon": base.flood_horizon,
        "race_halflife": base.race_halflife,
        "cover_boost": base.cover_boost,
        "cover_sigma": base.cover_sigma,
        "acquisition_budget": base.acquisition_budget,
        "cover_bankroll": base.cover_bankroll,
        "market_overround": base.market_overround,
        "acquired_firms": base.acquired_firms,
    }
    fields[knob] = value
    return metrics.MissionScenario(**fields)


def test_baseline_payload_is_reproducible() -> None:
    """Positive control for the liveness gate: identical scenarios agree.

    Without this, `test_every_scenario_knob_moves_a_metric` could pass on a
    payload that is simply nondeterministic.
    """
    assert metrics.run_mission_metrics(metrics.DEFAULT_SCENARIO) == metrics.run_mission_metrics(
        metrics.DEFAULT_SCENARIO
    )
    assert metrics.run_mission_metrics(_perturbed("cover_boost", metrics.DEFAULT_SCENARIO.cover_boost)) == (
        metrics.run_mission_metrics(metrics.DEFAULT_SCENARIO)
    )


@pytest.mark.parametrize(("knob", "value", "groups"), KNOB_PERTURBATIONS)
def test_every_scenario_knob_moves_a_metric(knob: str, value: Any, groups: tuple[str, ...]) -> None:
    """No knob may be inert: it must move *every* group that consumes it."""
    baseline = metrics.run_mission_metrics(metrics.DEFAULT_SCENARIO)
    changed = metrics.run_mission_metrics(_perturbed(knob, value))
    assert changed != baseline, f"scenario knob {knob!r} is inert — it changed nothing"
    for group in groups:
        assert changed[group] != baseline[group], f"knob {knob!r} did not reach metric group {group!r}"


# --------------------------------------------------------------- end-to-end tokens
#: Tokens that merely echo the config file back. A knob that moves only these
#: is still inert as far as the science is concerned.
_ECHO_PREFIXES = ("CONFIG_", "GENERATION_", "PYTHON_", "ZORIN_")


def _computed_tokens(variables: dict[str, str]) -> dict[str, str]:
    return {k: v for k, v in variables.items() if not k.startswith(_ECHO_PREFIXES)}


def test_config_edit_moves_computed_manuscript_tokens(tmp_path: Path) -> None:
    """The original falsifying experiment, run as a gate.

    Rewrite every experiment knob in a copy of the real config, hydrate the
    manuscript variables from it, and require the *computed* tokens to differ.
    Before the scenario was threaded into the models this assertion failed:
    every `CONFIG_*` token moved and not one computed token did.
    """
    config = copy.deepcopy(_config())
    config["experiment"].update(
        {
            "flood_ingress_rate": 3.0,
            "flood_horizon": 200.0,
            "race_halflife": 0.5,
            "cover_boost": 0.9,
            "cover_sigma": 0.15,
            "acquisition_budget": 1,
            "cover_bankroll": 25_000.0,
            "market_overround": 1.45,
            "scenario_acquired_firms": ["intel_fab", "nec_fab"],
        }
    )
    edited = tmp_path / "config.yaml"
    edited.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")

    baseline = _computed_tokens(msv.generate_variables())
    changed = _computed_tokens(msv.generate_variables(config_path=edited))

    moved = {key for key in baseline if baseline[key] != changed.get(key)}
    assert moved, "editing every experiment knob moved no computed token at all"
    # every knob has to leave a fingerprint on a *specific* computed token
    for token in (
        "FLOOD_FRACTION",  # ingress rate + horizon
        "RACE_TOP_RATING",  # halflife
        "COVER_WIN_DELTA",  # boost
        "COVER_DETECTION_RISK",  # sigma
        "ACQ_BUDGET",  # budget
        "MARKET_STAKE",  # bankroll
        "MARKET_IMPLIED",  # overround
        "SC_HHI_AFTER",  # acquisition set
    ):
        assert baseline[token] != changed[token], f"{token} did not respond to the config edit"


def test_single_knob_edit_moves_its_own_token(tmp_path: Path) -> None:
    """Per-knob end-to-end liveness, so a bulk edit cannot mask one dead knob."""
    expected_token = {
        "flood_ingress_rate": "FLOOD_VAULT_TIME",
        "flood_horizon": "FLOOD_FRACTION",
        "race_halflife": "RACE_TOP_RATING",
        "cover_boost": "COVER_WIN_DELTA",
        "cover_sigma": "COVER_DETECTION_RISK",
        "acquisition_budget": "ACQ_OPTIMAL_HHI",
        "cover_bankroll": "MARKET_STAKE",
        "market_overround": "MARKET_IMPLIED",
        "scenario_acquired_firms": "SC_HHI_AFTER",
    }
    values: dict[str, Any] = {
        "flood_ingress_rate": 3.0,
        "flood_horizon": 200.0,
        "race_halflife": 0.5,
        "cover_boost": 0.9,
        "cover_sigma": 0.15,
        "acquisition_budget": 1,
        "cover_bankroll": 25_000.0,
        "market_overround": 1.45,
        "scenario_acquired_firms": ["intel_fab", "nec_fab"],
    }
    baseline = msv.generate_variables()
    for knob, token in expected_token.items():
        config = copy.deepcopy(_config())
        config["experiment"][knob] = values[knob]
        edited = tmp_path / f"config_{knob}.yaml"
        edited.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
        changed = msv.generate_variables(config_path=edited)
        assert baseline[token] != changed[token], f"knob {knob!r} did not move token {token}"


# --------------------------------------------------------------- scenario validation
@pytest.mark.parametrize(
    ("knob", "bad"),
    [
        ("flood_ingress_rate", 0.0),
        ("flood_horizon", -1.0),
        ("race_halflife", 0.0),
        ("cover_sigma", 0.0),
        ("cover_boost", -0.1),
        ("cover_boost", "fast"),
        ("acquisition_budget", -1),
        ("acquisition_budget", 1.5),
        ("cover_bankroll", 0.0),
        ("cover_bankroll", "lots"),
        ("market_overround", 1.0),
        ("market_overround", "wide"),
        ("acquired_firms", ()),
        ("acquired_firms", ("",)),
        ("acquired_firms", ["amd_fab"]),
    ],
)
def test_scenario_rejects_invalid_knobs(knob: str, bad: Any) -> None:
    with pytest.raises(ValueError):
        _perturbed(knob, bad)


# --------------------------------------------------------------- scenario vs optimizer
def test_scenario_shortfall_is_the_optimizer_bound() -> None:
    """The optimizer bounds the scenario from above; the shortfall is real."""
    acq_m = metrics.acquisition_metrics()
    assert acq_m["scenario_shortfall"] == pytest.approx(acq_m["optimal_hhi"] - acq_m["scenario_hhi"])
    assert acq_m["scenario_shortfall"] >= 0.0
    # the reported scenario is genuinely a different set from the optimum,
    # which is the fact the manuscript's "Scenario versus optimizer" section
    # reports rather than reconciles away
    assert sorted(acq_m["scenario_acquired"]) != sorted(acq_m["optimal_acquired"])
    assert acq_m["scenario_shortfall"] > 0.0


def test_cascade_removed_and_retained_labels_match_the_computation() -> None:
    """The cascade's reported sets must be the sets the model actually used.

    `03_results.md` explains the zero starved fraction by naming which firms
    were removed and which were left standing. The prior text had it exactly
    backwards — it credited the *acquired* (i.e. removed) fabs with still
    supplying the assembly stage. Labels alone are cheap, so this test
    recomputes the cascade from the reported removed set and requires the
    reported starved fraction to come back out.
    """
    scenario = metrics.DEFAULT_SCENARIO
    chip_m = metrics.chip_metrics(scenario)
    chain = chip.build_default_supply_chain()

    # the removed set is the scenario's acquired-and-dismantled firms
    assert chip_m["cascade_removed"] == list(scenario.acquired_firms)
    assert chip_m["scenario_acquired"] == list(scenario.acquired_firms)

    # the retained fabricators are the fabrication-stage firms NOT removed
    all_fabs = {s.name for s in chain.suppliers if s.stage == "fabrication"}
    assert set(chip_m["cascade_retained_fabs"]) == all_fabs - set(chip_m["cascade_removed"])
    assert not set(chip_m["cascade_retained_fabs"]) & set(chip_m["cascade_removed"])

    # and re-running the model on the reported removed set reproduces the number
    starved, fraction = chip.cascade_starved(chain, chip_m["cascade_removed"])
    assert sorted(starved) == chip_m["cascade_starved_firms"]
    assert fraction == pytest.approx(chip_m["cascade_starved_fraction"])

    # negative control: the retained set is a genuinely different removal, so
    # the equality above is not true of any set we might have labelled
    _, other_fraction = chip.cascade_starved(chain, chip_m["cascade_retained_fabs"])
    assert other_fraction != pytest.approx(fraction)


def test_optimal_scenario_has_zero_shortfall() -> None:
    """Negative control: score the optimizer's own answer and the gap closes."""
    optimal = tuple(metrics.acquisition_metrics()["optimal_acquired"])
    scenario = _perturbed("acquired_firms", optimal)
    acq_m = metrics.acquisition_metrics(scenario)
    assert acq_m["scenario_shortfall"] == pytest.approx(0.0)
