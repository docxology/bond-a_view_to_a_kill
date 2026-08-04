"""ZORIN — special-agent mission software for *A View to a Kill* (1985).

A BOND-suite film package implementing the FROZEN
:class:`~bond_api.protocol.MissionProvider` contract around three pure domain
concepts:

* :mod:`a_view_to_a_kill.chip_supply_chain` — microchip supply-chain security
  graph (monopoly choke-point analysis).
* :mod:`a_view_to_a_kill.mine_flood` — flood-the-mine infrastructure
  sabotage model (water-ingress dynamics).
* :mod:`a_view_to_a_kill.race_analytics` — horse-race form analytics
  (cover-operation modeling).

``mission`` is the thin adapter to BOND-API; the three concept modules are
pure and importable without ``bond_api``.
"""

from __future__ import annotations

from a_view_to_a_kill import chip_supply_chain, mission, mine_flood, race_analytics

__all__ = [
    "chip_supply_chain",
    "mine_flood",
    "race_analytics",
    "mission",
]
