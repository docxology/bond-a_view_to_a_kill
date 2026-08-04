"""ZORIN manuscript variable hydration.

Every ``{{TOKEN}}`` in ``manuscript/*.md`` resolves through
:func:`generate_variables`, which reads ``manuscript/config.yaml`` plus the
deterministic mission metrics computed by the pure domain core. Metrics are
never hand-authored in prose: they flow through this module so the manuscript
cannot drift from the code.

This module is intentionally ``bond_api``-free: it imports only the three
concept modules (and mission's metric helpers, which likewise import no
protocol types), so the manuscript pipeline also works in the fallback where
the path dependency is unavailable. The consuming orchestrator is
``scripts/z_generate_manuscript_variables.py`` (thin wrapper); the live
cross-reference gate lives in ``tests/test_manuscript_variables.py``.
"""

from __future__ import annotations

import platform
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from a_view_to_a_kill import mission

__all__ = ["generate_variables", "load_manuscript_config", "resolve_manuscript_tree"]

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
        raise ValueError(f"manuscript config must be a top-level mapping, got {type(data).__name__}")
    return data


def _fmt(value: object, digits: int = 4) -> str:
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def generate_variables(
    *,
    config_path: str | Path | None = None,
    require_outputs: bool = True,
    now: datetime | None = None,
) -> dict[str, str]:
    """Compute the ``{{TOKEN}}`` → value mapping for the ZORIN manuscript.

    Args:
        config_path: Override for ``manuscript/config.yaml``.
        require_outputs: When True (default), verify the computed metric
            groups are populated — the strict-mode gate that the pipeline
            asserts before rendering.
        now: Optional clock override for a fully deterministic timestamp
            (tests pass a fixed value).
    """
    config = load_manuscript_config(config_path)
    paper = config.get("paper", {})
    if not isinstance(paper, dict):
        raise ValueError("manuscript config 'paper' section must be a mapping")
    experiment = config.get("experiment", {})
    if not isinstance(experiment, dict):
        raise ValueError("manuscript config 'experiment' section must be a mapping")

    metrics = mission.run_mission_metrics()
    if require_outputs and not metrics["chip"] and not metrics["flood"] and not metrics["race"]:
        raise ValueError("mission metrics are empty — the pure core failed to compute")

    chip_m = metrics["chip"]
    flood_m = metrics["flood"]
    race_m = metrics["race"]

    monkey = race_m["ratings"]
    top_rating = max(monkey.values())
    top_horse = max(monkey, key=monkey.get)

    stamp = (now or datetime.now(timezone.utc)).isoformat(timespec="seconds")

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
        # computed supply-chain metrics
        "SC_NODES": str(chip_m["nodes"]),
        "SC_LINKS": str(chip_m["links"]),
        "SC_HHI_BEFORE": _fmt(chip_m["hhi_before"], 1),
        "SC_HHI_AFTER": _fmt(chip_m["hhi_after"], 1),
        "SC_ZORIN_FAB_SHARE": _fmt(chip_m["zorin_fab_share"], 3),
        "SC_CASCADE_STARVED": _fmt(chip_m["cascade_starved_fraction"], 3),
        "SC_TOP_CHOKE": _fmt(chip_m["top_choke_points"][0][0], 0),
        # computed flood metrics
        "FLOOD_CHAMBERS": str(flood_m["chambers"]),
        "FLOOD_TUNNELS": str(flood_m["tunnels"]),
        "FLOOD_TOTAL_VOLUME": _fmt(flood_m["total_volume"], 0),
        "FLOOD_FRACTION": _fmt(flood_m["flooded_fraction"], 3),
        "FLOOD_CRITICAL_INGRESS": str(flood_m["critical_ingress"][0]),
        "FLOOD_WATER_BALANCE": "{:.1e}".format(float(flood_m["water_balance_error"])),
        "FLOOD_VAULT_TIME": _fmt(flood_m["vault_flood_time"], 1),
        # computed race/cover metrics
        "RACE_HORSES": str(race_m["horses"]),
        "RACE_RECORDS": str(race_m["records"]),
        "RACE_TOP_HORSE": top_horse,
        "RACE_TOP_RATING": _fmt(top_rating, 3),
        "RACE_PEGASUS_PROB": _fmt(race_m["win_probabilities"]["Pegasus"], 3),
        "COVER_WIN_DELTA": _fmt(race_m["pegasus_win_delta"], 3),
        "COVER_DETECTION_RISK": _fmt(race_m["detection_risk"], 3),
        "COVER_EXPECTED_VALUE": _fmt(race_m["expected_value"], 0),
        # environment
        "PYTHON_VERSION": platform.python_version(),
        "GENERATION_TIMESTAMP": stamp,
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
    manuscript_dir = Path(manuscript_dir) if manuscript_dir is not None else PACKAGE_ROOT / "manuscript"
    output_dir = Path(output_dir) if output_dir is not None else PACKAGE_ROOT / "output" / "manuscript"
    resolved: list[str] = []
    for source in sorted(manuscript_dir.glob("[0-9][0-9]_*.md")):
        text = source.read_text(encoding="utf-8")
        for token, value in variables.items():
            text = text.replace("{{" + token + "}}", value)
        unresolved = sorted(set(_TOKEN_RE.findall(text)))
        if unresolved and strict:
            raise ValueError(f"unresolved manuscript tokens in {source.name}: {unresolved}")
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / source.name).write_text(text, encoding="utf-8")
        resolved.append(source.name)
    return output_dir, resolved
