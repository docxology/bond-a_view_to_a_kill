"""ZORIN manuscript variable hydration.

Every ``{{TOKEN}}`` in ``manuscript/*.md`` resolves through
:func:`generate_variables`, which reads ``manuscript/config.yaml`` plus the
deterministic mission metrics computed by the pure domain core. Metrics are
never hand-authored in prose: they flow through this module so the manuscript
cannot drift from the code.

The config's ``experiment:`` knobs are not merely echoed as ``CONFIG_*``
tokens — they are converted to a :class:`a_view_to_a_kill.metrics.MissionScenario`
and used to *compute* the metrics, so editing a knob moves the computed
tokens too (``tests/test_metrics_scenario.py`` proves this end to end).

This module is ``bond_api``-free: it imports the pure concept modules and
:mod:`a_view_to_a_kill.metrics` (which is itself protocol-free), never
:mod:`a_view_to_a_kill.mission`. That is what makes the manuscript pipeline
work in the fallback where the ``bond-api`` path dependency is unavailable —
``tests/test_bond_api_fallback.py`` proves it rather than asserting it. The
consuming orchestrator is ``scripts/z_generate_manuscript_variables.py`` (thin
wrapper); the live cross-reference gate lives in
``tests/test_manuscript_variables.py``.

**No wall clock reaches a persisted artifact.** Every token is a function of
committed inputs only — ``manuscript/config.yaml``, the pure domain core, and
the interpreter version. The provenance date rendered into the manuscript
(``MANUSCRIPT_DATE``) is read from ``paper.date`` in the config, never from
``datetime.now()``. That is what makes the byte-identical-rerun claim in
``manuscript/02_methodology.md`` and ``manuscript/06_reproducibility.md`` true
rather than aspirational, and it is checked end to end by
``tests/test_regeneration_determinism.py``, which runs the real generator twice
in two processes and diffs the bytes. A ``now=``-injection test cannot
substitute for that: pinning the clock in-test proves only that a fixed input
gives a fixed output, which is why the wall-clock breach survived here for as
long as it did.
"""

from __future__ import annotations

import platform
import re
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import yaml

from a_view_to_a_kill import chip_supply_chain as chip_module
from a_view_to_a_kill import metrics as metrics_module
from a_view_to_a_kill import mine_flood as flood_module
from a_view_to_a_kill import race_analytics as race_module

__all__ = [
    "generate_variables",
    "load_manuscript_config",
    "package_module_names",
    "render_counts_markdown",
    "resolve_manuscript_tree",
]

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PACKAGE_ROOT / "manuscript" / "config.yaml"

_TOKEN_RE = re.compile(r"\{\{[A-Z0-9_]+\}\}")


def load_manuscript_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """Load and validate ``manuscript/config.yaml`` (or an explicit path)."""
    path = Path(config_path) if config_path is not None else DEFAULT_CONFIG_PATH
    if not path.is_file():
        raise FileNotFoundError(f"manuscript config not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(
            f"manuscript config must be a top-level mapping, got {type(data).__name__}"
        )
    return data


def _fmt(value: object, digits: int = 4) -> str:
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def _join(names: object) -> str:
    """Render a computed name list for prose; an empty set renders as ``none``.

    Prose that reads "the survivors are {{TOKEN}}" must not silently render an
    empty string when the computed set is empty — that would turn a real
    "nobody" result into a typographic accident.
    """
    items = [str(name) for name in (names if isinstance(names, (list, tuple)) else [])]
    return ", ".join(items) if items else "none"


#: The metric groups :func:`generate_variables` requires to be populated.
REQUIRED_METRIC_GROUPS = ("chip", "flood", "race", "acquisition", "valley", "market")


def generate_variables(
    *,
    config_path: str | Path | None = None,
    require_outputs: bool = True,
    metrics: dict[str, Any] | None = None,
) -> dict[str, str]:
    """Compute the ``{{TOKEN}}`` → value mapping for the ZORIN manuscript.

    Args:
        config_path: Override for ``manuscript/config.yaml``.
        require_outputs: When True (default), verify that **every** metric
            group in :data:`REQUIRED_METRIC_GROUPS` is populated — the
            strict-mode gate the pipeline asserts before rendering. Any one
            empty group fails; this is deliberately an ``any``-style check,
            because a single silently-empty group would otherwise render a
            manuscript with hollow numbers.
        metrics: Optional pre-computed metric payload (same shape as
            :func:`a_view_to_a_kill.metrics.run_mission_metrics`). Defaults to
            computing it live **from the config's scenario**; supplying it lets
            the strict gate be exercised against real degraded payloads without
            any mocking.

    Returns:
        A token → value mapping that is a pure function of committed inputs.
        There is deliberately no clock parameter: the module reads no wall
        clock at all, so two calls at different times return equal mappings
        (``tests/test_regeneration_determinism.py``).

    Raises:
        ValueError: If the config sections are malformed, ``paper.date`` is
            missing, an ``experiment:`` knob is missing, or a required metric
            group is missing/empty under ``require_outputs``.
    """
    config = load_manuscript_config(config_path)
    paper = config.get("paper", {})
    if not isinstance(paper, dict):
        raise ValueError("manuscript config 'paper' section must be a mapping")
    experiment = config.get("experiment", {})
    if not isinstance(experiment, dict):
        raise ValueError("manuscript config 'experiment' section must be a mapping")

    # The manuscript's provenance date is a *committed* value, not a clock
    # reading. It must be present: falling back to an empty string would put a
    # hollow "Manuscript source date  (UTC)" line on the page, and falling back
    # to `datetime.now()` is the exact defect this replaced.
    manuscript_date = str(paper.get("date", "")).strip()
    if not manuscript_date:
        raise ValueError(
            "manuscript config 'paper.date' is required — it is the manuscript's "
            "provenance stamp, and the pipeline reads no wall clock to substitute for it"
        )

    scenario = metrics_module.scenario_from_config(experiment)
    computed = (
        metrics_module.run_mission_metrics(scenario) if metrics is None else metrics
    )
    if require_outputs:
        empty = [group for group in REQUIRED_METRIC_GROUPS if not computed.get(group)]
        if empty:
            raise ValueError(
                f"mission metric groups are empty — the pure core failed to compute: {empty}"
            )

    chip_m = computed["chip"]
    flood_m = computed["flood"]
    race_m = computed["race"]
    acq_m = computed["acquisition"]
    valley_m = computed["valley"]
    market_m = computed["market"]

    ratings = race_m["ratings"]
    top_horse = max(sorted(ratings), key=lambda name: ratings[name])
    top_rating = ratings[top_horse]

    return {
        # identity from config
        "ZORIN_TITLE": str(paper.get("title", "")),
        "ZORIN_SUBTITLE": str(paper.get("subtitle", "")),
        "ZORIN_VERSION": str(paper.get("version", "")),
        "ZORIN_CODENAME": "ZORIN",
        "ZORIN_FILM": "A View to a Kill (1985)",
        "CONFIG_FIRST_AUTHOR": "Daniel Ari Friedman",
        "CONFIG_KEYWORDS": ", ".join(config.get("keywords", [])),
        "CONFIG_FLOOD_HORIZON": str(experiment.get("flood_horizon", "")),
        "CONFIG_FLOOD_INGRESS_RATE": str(experiment.get("flood_ingress_rate", "")),
        "CONFIG_RACE_HALFLIFE": str(experiment.get("race_halflife", "")),
        "CONFIG_COVER_BOOST": str(experiment.get("cover_boost", "")),
        "CONFIG_COVER_SIGMA": str(experiment.get("cover_sigma", "")),
        "CONFIG_ACQUISITION_BUDGET": str(experiment.get("acquisition_budget", "")),
        "CONFIG_COVER_BANKROLL": str(experiment.get("cover_bankroll", "")),
        "CONFIG_MARKET_OVERROUND": str(experiment.get("market_overround", "")),
        # computed supply-chain metrics
        "SC_NODES": str(chip_m["nodes"]),
        "SC_LINKS": str(chip_m["links"]),
        "SC_HHI_BEFORE": _fmt(chip_m["hhi_before"], 1),
        "SC_HHI_AFTER": _fmt(chip_m["hhi_after"], 1),
        "SC_ZORIN_FAB_SHARE": _fmt(chip_m["zorin_fab_share"], 3),
        "SC_CASCADE_STARVED": _fmt(chip_m["cascade_starved_fraction"], 3),
        "SC_TOP_CHOKE": _fmt(chip_m["top_choke_points"][0][0], 0),
        # the scenario's acquisition set and the cascade's actual removed /
        # retained sets — emitted so prose never names a firm by hand
        "SC_SCENARIO_ACQUIRED": _join(chip_m["scenario_acquired"]),
        "SC_SCENARIO_ACQUIRED_COUNT": str(len(chip_m["scenario_acquired"])),
        "SC_CASCADE_REMOVED": _join(chip_m["cascade_removed"]),
        "SC_CASCADE_RETAINED_FABS": _join(chip_m["cascade_retained_fabs"]),
        "SC_CASCADE_STARVED_FIRMS": _join(chip_m["cascade_starved_firms"]),
        # computed acquisition metrics
        "ACQ_BUDGET": str(acq_m["budget"]),
        "ACQ_ACQUIREABLE": ", ".join(acq_m["acquireable"]),
        "ACQ_OPTIMAL_ACQUIRED": ", ".join(acq_m["optimal_acquired"]),
        "ACQ_OPTIMAL_HHI": _fmt(acq_m["optimal_hhi"], 1),
        "ACQ_OPTIMAL_FAB_SHARE": _fmt(acq_m["optimal_fab_share"], 3),
        "ACQ_BASELINE_HHI": _fmt(acq_m["baseline_hhi"], 1),
        "ACQ_HHI_GAIN": _fmt(acq_m["hhi_gain"], 1),
        "ACQ_GREEDY_HHI": _fmt(acq_m["greedy_hhi"], 1),
        "ACQ_REGRET": _fmt(acq_m["regret"], 1),
        # scenario-vs-optimizer reconciliation
        "ACQ_SCENARIO_ACQUIRED": _join(acq_m["scenario_acquired"]),
        "ACQ_SCENARIO_SIZE": str(acq_m["scenario_size"]),
        "ACQ_SCENARIO_HHI": _fmt(acq_m["scenario_hhi"], 1),
        "ACQ_SCENARIO_FAB_SHARE": _fmt(acq_m["scenario_fab_share"], 3),
        "ACQ_SCENARIO_SHORTFALL": _fmt(acq_m["scenario_shortfall"], 1),
        # computed flood metrics
        "FLOOD_CHAMBERS": str(flood_m["chambers"]),
        "FLOOD_TUNNELS": str(flood_m["tunnels"]),
        "FLOOD_TOTAL_VOLUME": _fmt(flood_m["total_volume"], 0),
        "FLOOD_FRACTION": _fmt(flood_m["flooded_fraction"], 3),
        "FLOOD_CRITICAL_INGRESS": str(flood_m["critical_ingress"][0]),
        "FLOOD_WATER_BALANCE": "{:.1e}".format(float(flood_m["water_balance_error"])),
        "FLOOD_VAULT_TIME": _fmt(flood_m["vault_flood_time"], 1),
        # computed valley-impact metrics
        "VALLEY_FABS": str(valley_m["fabs"]),
        "VALLEY_LOSS": _fmt(valley_m["capacity_loss"], 3),
        "VALLEY_INOPERABLE": str(valley_m["inoperable"]),
        "VALLEY_VICTIMS": _join(valley_m["victims"]),
        "VALLEY_SURVIVORS": _join(valley_m["survivors"]),
        "VALLEY_SURVIVOR_COUNT": str(len(valley_m["survivors"])),
        # ownership split of the flood's outcome — computed set operations, so
        # the manuscript's "who does the flood spare" claim cannot go stale
        "VALLEY_ACQUIRED_VICTIMS": _join(valley_m["acquired_victims"]),
        "VALLEY_ACQUIRED_SURVIVORS": _join(valley_m["acquired_survivors"]),
        "VALLEY_UNACQUIRED_VICTIMS": _join(valley_m["unacquired_victims"]),
        "VALLEY_UNACQUIRED_SURVIVORS": _join(valley_m["unacquired_survivors"]),
        "VALLEY_UNACQUIRED_SURVIVOR_COUNT": str(len(valley_m["unacquired_survivors"])),
        # computed race/cover metrics
        "RACE_HORSES": str(race_m["horses"]),
        "RACE_RECORDS": str(race_m["records"]),
        "RACE_RACES_PER_HORSE": str(race_m["records"] // race_m["horses"]),
        "RACE_TOP_HORSE": top_horse,
        "RACE_TOP_RATING": _fmt(top_rating, 3),
        "RACE_PEGASUS_PROB": _fmt(race_m["win_probabilities"]["Pegasus"], 3),
        "COVER_WIN_DELTA": _fmt(race_m["pegasus_win_delta"], 3),
        "COVER_DETECTION_RISK": _fmt(race_m["detection_risk"], 3),
        "COVER_EXPECTED_VALUE": _fmt(race_m["expected_value"], 0),
        # computed market/cover-finance metrics
        "MARKET_HORSE": market_m["horse"],
        "MARKET_TRUE_PROB": _fmt(market_m["true_probability"], 3),
        "MARKET_IMPLIED": _fmt(market_m["market_implied_probability"], 3),
        "MARKET_EDGE": _fmt(market_m["value_edge"], 4),
        "MARKET_KELLY": _fmt(market_m["kelly_fraction"], 4),
        "MARKET_STAKE": _fmt(market_m["kelly_stake"], 0),
        "MARKET_PROFIT": _fmt(market_m["expected_profit"], 0),
        # model constants read straight off the pure core, so prose can cite
        # them without a hand-authored numeral that could silently drift
        "CORE_DISCHARGE_COEFF": _fmt(flood_module.DEFAULT_DISCHARGE, 2),
        "CORE_EULER_DT": _fmt(metrics_module.FLOOD_DT, 1),
        "CORE_DETECTION_THRESHOLD": _fmt(race_module.DETECTION_THRESHOLD, 1),
        "CORE_PAR_SECONDS": _fmt(race_module.PAR_SECONDS_PER_FURLONG, 1),
        "CORE_BASE_WEIGHT": _fmt(race_module.BASE_WEIGHT, 0),
        "CORE_WEIGHT_SEC_PER_LB": _fmt(race_module.WEIGHT_SECONDS_PER_LB, 2),
        "CORE_PURSE": _fmt(race_module.PURSE, 0),
        "CORE_DETECTION_PENALTY": _fmt(race_module.DETECTION_PENALTY, 0),
        "CORE_MISSION_SEED": str(metrics_module.SEED),
        "CORE_STAGES": ", ".join(chip_module.STAGES),
        # environment + provenance. Both are functions of committed inputs and
        # the pinned interpreter — neither reads a clock, so reruns on one
        # toolchain are byte-identical.
        "PYTHON_VERSION": platform.python_version(),
        "MANUSCRIPT_DATE": manuscript_date,
    }


def resolve_manuscript_tree(
    variables: dict[str, str],
    *,
    manuscript_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
    strict: bool = True,
) -> tuple[Path, list[str]]:
    """Copy each manuscript section to ``output/manuscript/``, substituting tokens.

    Only ``NN_*.md`` section files are copied (not sidecars such as
    ``SYNTAX.md``). In strict mode any leftover ``{{TOKEN}}`` fails the
    resolution so the manuscript can never render with raw braces.

    Returns the output directory and the sorted list of resolved file names.
    """
    manuscript_dir = (
        Path(manuscript_dir)
        if manuscript_dir is not None
        else PACKAGE_ROOT / "manuscript"
    )
    output_dir = (
        Path(output_dir)
        if output_dir is not None
        else PACKAGE_ROOT / "output" / "manuscript"
    )
    resolved: list[str] = []
    for source in sorted(manuscript_dir.glob("[0-9][0-9]_*.md")):
        text = source.read_text(encoding="utf-8")
        for token, value in variables.items():
            text = text.replace("{{" + token + "}}", value)
        unresolved = sorted(set(_TOKEN_RE.findall(text)))
        if unresolved and strict:
            raise ValueError(
                f"unresolved manuscript tokens in {source.name}: {unresolved}"
            )
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / source.name).write_text(text, encoding="utf-8")
        resolved.append(source.name)
    return output_dir, resolved


#: Rows that record a measurement of a coverage run rather than of the source
#: tree. The renderer cannot derive them (a suite cannot measure its own coverage
#: from inside itself), so they are recorded here, dated, and the CLI overrides
#: them from a fresh run.
_RECORDED_COUNTS: dict[str, str | int | tuple[str, ...]] = {
    "coverage": "100.00%",
    "skipped_failed": "0 / 0",
    "lowest_covered": "none — every module at 100%",
    "uncovered": (
        "0 (the six unreachable defensive guards were closed with "
        "`# pragma: no cover` + rationale; see `TODO.md` Round-2 C1)"
    ),
    "pure_modules": (
        "chip_supply_chain",
        "acquisition",
        "mine_flood",
        "valley_impact",
        "race_analytics",
        "race_market",
    ),
    "metric_layer": (
        "`metrics` (six groups: chip / flood / race / acquisition / valley / market)"
    ),
    "tokens": 87,
    "figures": 5,
}

#: Date of the gate run the recorded rows above were read from.
RECORDED_COUNTS_DATE = "2026-11-03"


def package_module_names() -> list[str]:
    """The package's module set, read off disk (the ``__init__`` files excluded).

    This is the inventory the counts document reports. Reading it off the tree is
    what makes that row a measurement rather than a second list someone has to
    remember to update.
    """
    package_dir = Path(__file__).resolve().parent
    return sorted(
        path.relative_to(package_dir).with_suffix("").as_posix()
        for path in package_dir.rglob("*.py")
        if path.name != "__init__.py"
    )


def _counts_cell(value: str | int | Sequence[str]) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, int):
        return str(value)
    return ", ".join(f"`{name}`" for name in value)


def render_counts_markdown(
    *,
    modules: Sequence[str],
    gadgets: Sequence[str],
    tests: int | None = None,
    **overrides: str | int | tuple[str, ...],
) -> str:
    """Render ``docs/_generated/COUNTS.md`` for the live package.

    ``modules`` and ``gadgets`` are read live by the caller
    (:func:`package_module_names` and the mission's ``gadget_registry``); this
    module stays ``bond_api``-free and cannot import the registry itself. Any key
    of the recorded rows may be overridden with what a real gate run printed, and
    an omitted key keeps its recorded value.
    """
    unknown = sorted(set(overrides) - set(_RECORDED_COUNTS))
    if unknown:
        raise ValueError(f"unknown counts row(s): {', '.join(unknown)}")
    rows = {**_RECORDED_COUNTS, **overrides}
    if tests is None:
        tests_cell = "not recorded — see the enforced gate below"
    else:
        tests_cell = str(tests)
    return "\n".join(
        [
            "# Live counts — a_view_to_a_kill (ZORIN)",
            "",
            "Hand-editing this file is not how it changes: `render_counts_markdown`",
            "in `src/a_view_to_a_kill/manuscript_variables.py` renders it, and",
            "`tests/test_counts_document.py` fails when the file and a fresh render",
            "disagree.",
            "",
            "The module and gadget rows are read live off the package, and the test",
            "count is asserted against the suite's own collection, so adding a test",
            "fails the suite until this file is regenerated. The coverage, token,",
            "figure and inventory rows record real runs on",
            f"{RECORDED_COUNTS_DATE} (the token and figure rows come from",
            "`scripts/z_generate_manuscript_variables.py`) and are not re-derived by",
            "that test: a suite cannot measure its own coverage from inside itself.",
            "The counts were last re-measured in the regeneration-determinism pass",
            "that replaced the wall-clock `GENERATION_TIMESTAMP` with the",
            "config-sourced `MANUSCRIPT_DATE`.",
            "",
            "| Metric | Value (measured) |",
            "|---|---|",
            f"| Passing tests | {tests_cell} |",
            f"| Skipped / failed | {_counts_cell(rows['skipped_failed'])} |",
            f"| Line + branch coverage on `src/` | {_counts_cell(rows['coverage'])} |",
            f"| Modules at 100% coverage | all {len(modules)}: {_counts_cell(modules)} |",
            f"| Lowest-covered module | {_counts_cell(rows['lowest_covered'])} |",
            f"| Uncovered statements remaining | {_counts_cell(rows['uncovered'])} |",
            f"| Pure domain modules | {_counts_cell(rows['pure_modules'])} |",
            f"| Metric layer | {_counts_cell(rows['metric_layer'])} |",
            f"| Mission gadgets | {_counts_cell(tuple(gadgets))} |",
            f"| Manuscript tokens resolved | {_counts_cell(rows['tokens'])} |",
            f"| Figures rendered | {_counts_cell(rows['figures'])} |",
            "",
            "Re-measure with:",
            "",
            "```bash",
            "uv run pytest tests/ --cov=src --cov-fail-under=90 -q",
            "uv run python scripts/z_generate_counts.py --tests <N> --coverage <PCT>",
            "```",
            "",
            "Test count alone: `uv run pytest tests/ --collect-only -q | tail -1`.",
            "Token and figure counts: `uv run python scripts/z_generate_manuscript_variables.py`.",
            "",
        ]
    )
