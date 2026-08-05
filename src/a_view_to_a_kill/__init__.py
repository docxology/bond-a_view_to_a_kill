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

``mission`` is the thin adapter to BOND-API; the concept modules are pure and
importable without ``bond_api``.
"""

from __future__ import annotations

from a_view_to_a_kill import (
    acquisition,
    chip_supply_chain,
    mine_flood,
    mission,
    race_analytics,
    race_market,
    valley_impact,
)

__all__ = [
    "acquisition",
    "chip_supply_chain",
    "mine_flood",
    "mission",
    "race_analytics",
    "race_market",
    "valley_impact",
]
