"""The claim ledger must record provenance, never a second copy of a number.

`data/claim_ledger.yaml` used to carry hand-authored metric strings ("892.2 /
1528.9", "0.680", "capacity loss 0.583", ...). Nothing checked them against
the code, so they were a second, ungated source of truth sitting directly
underneath the guardrail "no hand-authored metric — every number is a token".
Several had already gone stale relative to the live computation.

The ledger now records generators and manuscript *token names* only. These
gates keep it that way:

* every token it names must resolve in ``generate_variables()`` — a renamed
  token breaks the ledger loudly instead of leaving a dangling reference;
* no ``value:`` key may reappear under ``model_datasets`` or
  ``computed_metrics`` — reintroducing a frozen numeral fails the suite;
* every entry must name a generator, so a claim can always be traced to code.

``film_facts`` is exempt from the ``value:`` ban on purpose: it records a
statement about the film, which is not a computed quantity.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest
import yaml

from a_view_to_a_kill import manuscript_variables as msv

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = PACKAGE_ROOT / "data" / "claim_ledger.yaml"

#: The sections that must stay numeral-free (they describe computed things).
COMPUTED_SECTIONS = ("model_datasets", "computed_metrics")


def _ledger() -> dict[str, Any]:
    return yaml.safe_load(LEDGER_PATH.read_text(encoding="utf-8"))


def _entries(section: str) -> list[dict[str, Any]]:
    return list(_ledger().get(section, []))


def test_ledger_parses_and_has_the_expected_sections() -> None:
    ledger = _ledger()
    for section in (*COMPUTED_SECTIONS, "film_facts"):
        assert section in ledger, f"claim ledger is missing section {section!r}"
        assert ledger[section], f"claim ledger section {section!r} is empty"


@pytest.mark.parametrize("section", COMPUTED_SECTIONS)
def test_ledger_records_no_frozen_numerals(section: str) -> None:
    """A ``value:`` key here would be an ungated second source of truth."""
    offenders = [entry["id"] for entry in _entries(section) if "value" in entry]
    assert not offenders, (
        f"claim ledger {section} entries {offenders} carry a hand-authored 'value:'. "
        "Record the token name instead — the number lives in the code."
    )


@pytest.mark.parametrize("section", COMPUTED_SECTIONS)
def test_every_ledger_entry_names_a_generator_and_tokens(section: str) -> None:
    for entry in _entries(section):
        key = "generator" if section == "computed_metrics" else "source"
        assert entry.get(key), f"{section}/{entry.get('id')} has no {key}"
        assert entry.get("tokens"), f"{section}/{entry.get('id')} names no manuscript tokens"


@pytest.mark.parametrize("section", COMPUTED_SECTIONS)
def test_every_ledger_token_resolves(section: str) -> None:
    """A ledger token that does not exist is a dangling provenance reference."""
    variables = msv.generate_variables(now=datetime(2026, 8, 1, tzinfo=timezone.utc))
    dangling: list[str] = []
    for entry in _entries(section):
        for token in entry["tokens"]:
            if token not in variables:
                dangling.append(f"{entry['id']}:{token}")
    assert not dangling, f"claim ledger names tokens that generate_variables() does not produce: {dangling}"


def test_ledger_covers_the_scenario_and_ownership_reconciliations() -> None:
    """The two findings the manuscript reports must be traceable in the ledger.

    Both are load-bearing negative results (the scheme is suboptimal; the flood
    destroys an acquired plant), so they need provenance like any other claim.
    """
    ids = {entry["id"] for entry in _entries("computed_metrics")}
    assert "scenario_vs_optimizer" in ids
    assert "valley_ownership_split" in ids
