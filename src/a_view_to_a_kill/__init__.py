"""ZORIN — special-agent mission software for *A View to a Kill* (1985).

A BOND-suite film package implementing the FROZEN
:class:`~bond_api.protocol.MissionProvider` contract around six pure domain
concepts:

* :mod:`a_view_to_a_kill.chip_supply_chain` — microchip supply-chain security
  graph (monopoly choke-point analysis).
* :mod:`a_view_to_a_kill.acquisition` — monopoly acquisition optimizer
  (exhaustive vs greedy, budget-constrained corner).
* :mod:`a_view_to_a_kill.mine_flood` — flood-the-mine infrastructure
  sabotage model (water-ingress dynamics).
* :mod:`a_view_to_a_kill.valley_impact` — urban sabotage coupling: mine-flood
  to surface-fab damage above Silicon Valley.
* :mod:`a_view_to_a_kill.race_analytics` — horse-race form analytics
  (cover-operation modeling).
* :mod:`a_view_to_a_kill.race_market` — racing betting-market / cover-finance
  analytics (odds, Kelly staking, value edge).

:mod:`a_view_to_a_kill.metrics` aggregates the six concepts into the mission's
deterministic metric payload and is itself protocol-free.
:mod:`a_view_to_a_kill.mission` is the thin BOND-API adapter and the *only*
module that imports ``bond_api``.

``mission`` is therefore resolved lazily (PEP 562): importing this package, or
any pure concept module through it, must not require ``bond-api`` to be
installed. ``a_view_to_a_kill.mission`` still works both as an attribute and
as a submodule import — the public shape is unchanged, only the import timing
is. ``tests/test_bond_api_fallback.py`` pins this behavior.
"""

from __future__ import annotations

import importlib
from types import ModuleType

from a_view_to_a_kill import (
    acquisition,
    chip_supply_chain,
    metrics,
    mine_flood,
    race_analytics,
    race_market,
    valley_impact,
)

__all__ = [
    "acquisition",
    "chip_supply_chain",
    "metrics",
    "mine_flood",
    "mission",
    "race_analytics",
    "race_market",
    "valley_impact",
]

#: Submodules resolved on first attribute access rather than at package import.
LAZY_SUBMODULES = ("mission",)


def __getattr__(name: str) -> ModuleType:
    """Resolve the ``bond_api``-dependent adapter on first attribute access."""
    if name in LAZY_SUBMODULES:
        module = importlib.import_module(f"{__name__}.{name}")
        globals()[name] = module
        return module
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    """Keep ``dir()`` and tab-completion aware of the lazily-loaded adapter."""
    return sorted(set(globals()) | set(__all__))
