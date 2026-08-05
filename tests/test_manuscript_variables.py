"""Tests for ZORIN manuscript variable hydration (manuscript_variables.py)."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml

from a_view_to_a_kill import manuscript_variables as msv
from a_view_to_a_kill import metrics
from a_view_to_a_kill import mission
from a_view_to_a_kill import race_analytics as race

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT = PACKAGE_ROOT / "manuscript"

_TOKEN_RE = re.compile(r"\{\{[A-Z0-9_]+\}\}")


def test_load_manuscript_config_loads_yaml() -> None:
    config = msv.load_manuscript_config()
    assert config["paper"]["title"].startswith("A View to a Kill")
    assert "keywords" in config


def test_load_manuscript_config_missing_file_raises() -> None:
    with pytest.raises(FileNotFoundError):
        msv.load_manuscript_config(MANUSCRIPT / "does_not_exist.yaml")


def test_load_manuscript_config_non_mapping_raises(tmp_path: Path) -> None:
    bogus = tmp_path / "config.yaml"
    bogus.write_text("just a string\n", encoding="utf-8")
    with pytest.raises(ValueError):
        msv.load_manuscript_config(bogus)


def test_generate_variables_returns_expected_tokens() -> None:
    variables = msv.generate_variables(require_outputs=True, now=datetime(2026, 8, 1, tzinfo=timezone.utc))
    for key in (
        "ZORIN_TITLE",
        "ZORIN_CODENAME",
        "ZORIN_FILM",
        "SC_NODES",
        "SC_HHI_BEFORE",
        "FLOOD_FRACTION",
        "RACE_TOP_HORSE",
        "COVER_DETECTION_RISK",
        "ACQ_OPTIMAL_HHI",
        "VALLEY_LOSS",
        "MARKET_KELLY",
        "PYTHON_VERSION",
        "GENERATION_TIMESTAMP",
    ):
        assert key in variables
        assert variables[key] != ""
    assert variables["ZORIN_CODENAME"] == "ZORIN"
    # timestamp must be an ISO 8601 string (contains a 'T' and a timezone)
    assert "T" in variables["GENERATION_TIMESTAMP"]
    assert "+" in variables["GENERATION_TIMESTAMP"]


def test_generate_variables_now_override_is_deterministic() -> None:
    stamp = datetime(2026, 8, 1, 12, 0, 0, tzinfo=timezone.utc)
    a = msv.generate_variables(now=stamp)["GENERATION_TIMESTAMP"]
    b = msv.generate_variables(now=stamp)["GENERATION_TIMESTAMP"]
    assert a == b == "2026-08-01T12:00:00+00:00"


def test_metrics_are_live_not_stale() -> None:
    variables = msv.generate_variables()
    # The flood fraction must be a real *partial* flood from the simulation:
    # strictly between "nothing flooded" and "everything flooded". A string
    # containment check would pass on a hollow 0.000, so parse and bound it.
    fraction = float(variables["FLOOD_FRACTION"])
    assert 0.0 < fraction < 1.0
    # The top-rated horse must be one of the horses actually on the card.
    assert variables["RACE_TOP_HORSE"] in {r.horse for r in race.FORM_TABLE}
    assert float(variables["RACE_TOP_RATING"]) > 0.0


def test_strict_gate_rejects_each_empty_metric_group() -> None:
    """The require_outputs gate must fail on *any* empty group, not only all.

    Uses a really-computed payload with one group blanked — no mocking, the
    remaining five groups are the genuine values from the pure core.
    """
    live = mission.run_mission_metrics()
    for group in msv.REQUIRED_METRIC_GROUPS:
        degraded = dict(live)
        degraded[group] = {}
        with pytest.raises(ValueError, match="mission metric groups are empty"):
            msv.generate_variables(metrics=degraded, require_outputs=True)


def test_draft_mode_skips_the_gate_and_still_renders_present_groups() -> None:
    """require_outputs=False is the --allow-draft path: no gate, real values."""
    live = mission.run_mission_metrics()
    variables = msv.generate_variables(metrics=live, require_outputs=False)
    assert variables["SC_NODES"] == str(live["chip"]["nodes"])
    assert variables["VALLEY_FABS"] == str(live["valley"]["fabs"])


def test_strict_gate_accepts_the_live_payload() -> None:
    """Positive control: the same gate passes on the undegraded payload."""
    live = mission.run_mission_metrics()
    variables = msv.generate_variables(metrics=live, require_outputs=True)
    assert variables["SC_NODES"] == str(live["chip"]["nodes"])


def test_generate_variables_rejects_non_mapping_paper_section(tmp_path: Path) -> None:
    bogus = tmp_path / "config.yaml"
    bogus.write_text("paper: not-a-mapping\nexperiment: {}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="'paper' section"):
        msv.generate_variables(config_path=bogus)


def test_generate_variables_rejects_non_mapping_experiment_section(tmp_path: Path) -> None:
    bogus = tmp_path / "config.yaml"
    bogus.write_text("paper: {title: t}\nexperiment: not-a-mapping\n", encoding="utf-8")
    with pytest.raises(ValueError, match="'experiment' section"):
        msv.generate_variables(config_path=bogus)


def test_every_manuscript_token_is_generated() -> None:
    """Live cross-reference gate: every {{TOKEN}} in prose sections resolves."""
    variables = msv.generate_variables(now=datetime(2026, 8, 1, tzinfo=timezone.utc))
    unresolved: list[str] = []
    for source in sorted(MANUSCRIPT.glob("[0-9][0-9]_*.md")):
        text = source.read_text(encoding="utf-8")
        for token in sorted(set(_TOKEN_RE.findall(text))):
            name = token[2:-2]  # strip the {{ }} delimiters
            if name not in variables:
                unresolved.append(f"{source.name}:{name}")
    assert not unresolved, f"tokens missing from generate_variables: {unresolved}"


def test_resolve_manuscript_tree_substitutes_and_writes(tmp_path: Path) -> None:
    variables = msv.generate_variables(now=datetime(2026, 8, 1, tzinfo=timezone.utc))
    out_dir, resolved = msv.resolve_manuscript_tree(variables, output_dir=tmp_path)
    assert out_dir == tmp_path
    assert resolved == sorted(m.name for m in MANUSCRIPT.glob("[0-9][0-9]_*.md"))
    sample = tmp_path / "00_abstract.md"
    assert sample.exists()
    text = sample.read_text(encoding="utf-8")
    assert "{{" not in text  # fully resolved


def test_resolve_manuscript_tree_strict_rejects_leftover_token(tmp_path: Path) -> None:
    md = MANUSCRIPT / "00_abstract.md"
    original = md.read_text(encoding="utf-8")
    try:
        md.write_text(original + "\n{{UNKNOWN_TOKEN_XYZ}}\n", encoding="utf-8")
        with pytest.raises(ValueError):
            msv.resolve_manuscript_tree({"A": "b"}, output_dir=tmp_path)
    finally:
        md.write_text(original, encoding="utf-8")


def test_config_has_expected_experiment_keys() -> None:
    config = yaml.safe_load((MANUSCRIPT / "config.yaml").read_text(encoding="utf-8"))
    exp = config["experiment"]
    for key in (
        "flood_ingress_rate",
        "flood_horizon",
        "race_halflife",
        "cover_boost",
        "cover_sigma",
        "acquisition_budget",
        "cover_bankroll",
        "market_overround",
        "scenario_acquired_firms",
    ):
        assert key in exp


def test_valley_ownership_split_matches_the_manuscript_claim() -> None:
    """Bind the results claim about *who the flood spares* to the computation.

    `03_results.md` states, in both directions, that the flood spares no plant
    outside ZORIN's control while destroying one he acquires. Both halves are
    computed set operations; this test recomputes them from the metric layer
    and fails the moment either stops holding, so the paragraph cannot outlive
    its data. (The prior text claimed "an unacquired rival survives", which
    the computed survivor set never supported.)
    """
    # Bind to the *config's* scenario, which is what hydrates the manuscript.
    config = yaml.safe_load((MANUSCRIPT / "config.yaml").read_text(encoding="utf-8"))
    scenario = metrics.scenario_from_config(config["experiment"])
    valley_m = metrics.valley_metrics(scenario)
    acquired = set(scenario.acquired_firms)
    victims = set(valley_m["victims"])
    survivors = set(valley_m["survivors"])

    # the sets are a real partition of the modelled fabs
    assert victims and survivors
    assert not victims & survivors
    assert len(victims | survivors) == valley_m["fabs"]

    # the split reported in the tokens is exactly the set arithmetic
    assert set(valley_m["acquired_victims"]) == victims & acquired
    assert set(valley_m["acquired_survivors"]) == survivors & acquired

    # direction 1: at least one plant ZORIN acquires is destroyed anyway
    assert valley_m["acquired_victims"], "manuscript claims the flood destroys a plant ZORIN acquires"
    # direction 2: no plant outside ZORIN's control survives
    assert valley_m["unacquired_survivors"] == [], (
        "manuscript claims no unacquired rival survives; computed survivors outside "
        f"ZORIN's control: {valley_m['unacquired_survivors']}"
    )


def test_scenario_acquisition_names_are_never_hand_written_in_prose() -> None:
    """Scenario-dependent firm names must reach the page as tokens.

    The results section used to name `amd_fab` and `nec_fab` in prose, which
    silently pinned the text to one config value. Any firm in the scenario's
    acquisition set must now arrive via {{SC_SCENARIO_ACQUIRED}} (or a
    sibling token), never as a literal.
    """
    config = yaml.safe_load((MANUSCRIPT / "config.yaml").read_text(encoding="utf-8"))
    scenario = metrics.scenario_from_config(config["experiment"])
    literals: list[str] = []
    for source in sorted(MANUSCRIPT.glob("[0-9][0-9]_*.md")):
        text = source.read_text(encoding="utf-8")
        for firm in scenario.acquired_firms:
            if firm in text:
                literals.append(f"{source.name}:{firm}")
    assert not literals, f"scenario acquisition firms hand-written in prose: {literals}"


def test_reproducibility_section_names_the_module_actually_called() -> None:
    """The manuscript must not claim the pipeline calls `mission`.

    `manuscript_variables` deliberately calls `metrics.run_mission_metrics()`;
    calling `mission` would import `bond_api` and break the fallback the same
    section asserts. The doc said `mission.run_mission_metrics()`.
    """
    source = (PACKAGE_ROOT / "src" / "a_view_to_a_kill" / "manuscript_variables.py").read_text(encoding="utf-8")
    assert "from a_view_to_a_kill import mission" not in source
    assert "metrics_module.run_mission_metrics" in source

    doc = (MANUSCRIPT / "06_reproducibility.md").read_text(encoding="utf-8")
    assert "mission.run_mission_metrics()" not in doc
    assert "metrics.run_mission_metrics(scenario)" in doc
