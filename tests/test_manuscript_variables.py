"""Tests for ZORIN manuscript variable hydration (manuscript_variables.py)."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml

from a_view_to_a_kill import manuscript_variables as msv

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
    # flood fraction must be a real partial-flood value from the simulation
    assert "0." in variables["FLOOD_FRACTION"]


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
    for key in ("flood_ingress_rate", "flood_horizon", "race_halflife", "cover_boost", "cover_sigma"):
        assert key in exp
