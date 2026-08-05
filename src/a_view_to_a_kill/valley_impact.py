"""Valley impact — mine-flood to Silicon Valley surface-fab damage coupling.

ZORIN's urban sabotage is not the flood itself but its *consequence*: the
flooded mine workings sit directly beneath Silicon Valley, and rising
groundwater migrates up through the fractured ground to undermine the
competing microchip fabrication plants built above. This module computes that
coupling.

Model:
* A :class:`SurfaceFab` sits above the mine, hydraulically coupled to a
  specific chamber. Water in that chamber raises the local water table; the
  fab's ``leakage`` (0..1) is the fraction of the chamber's head that
  transmits to its foundation.
* Water-table elevation under a fab at time ``t`` is
  ``leakage * coupled_chamber_level(t)``, where ``coupled_chamber_level`` is
  the chamber's free-surface elevation recovered from a
  :class:`~a_view_to_a_kill.mine_flood.FloodResult`.
* The fab becomes **inoperable** once its water table reaches its
  ``foundation_elevation``; :func:`fab_inoperable_at` returns the earliest
  such time.
* :func:`valley_capacity_loss` reports the fraction of total fabricating
  capacity inoperable by a decision time — the blast-reach of the planned
  flood on the city above.

Pure domain logic: imports only ``mine_flood``; no I/O, no randomness, no
``bond_api``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Iterable

from a_view_to_a_kill import mine_flood as flood

__all__ = [
    "SurfaceFab",
    "build_default_valley",
    "chamber_level_at",
    "fab_water_table",
    "fab_inoperable_at",
    "valley_capacity_loss",
    "valley_report",
]


@dataclass(frozen=True)
class SurfaceFab:
    """A microchip fabrication plant above the flooded mine.

    Attributes:
        name: Fab identifier (mirrors a supply-chain fabricator).
        capacity: Fabricating capacity (thousands of units/quarter).
        chamber: The mine chamber this fab is hydraulically coupled to.
        foundation_elevation: Groundwater elevation (m above datum) at which
            the fab's foundation is flooded and it becomes inoperable.
        leakage: Hydraulic coupling coefficient (0..1) — fraction of the
            coupled chamber's head transmitted to the foundation.
    """

    name: str
    capacity: float
    chamber: str
    foundation_elevation: float
    leakage: float

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("SurfaceFab.name must be a non-empty string")
        if not isinstance(self.capacity, (int, float)) or isinstance(self.capacity, bool):
            raise ValueError(f"SurfaceFab {self.name!r} capacity must be a number")
        if self.capacity <= 0:
            raise ValueError(f"SurfaceFab {self.name!r} capacity must be positive")
        if not isinstance(self.chamber, str) or not self.chamber.strip():
            raise ValueError(f"SurfaceFab {self.name!r} chamber must be a non-empty string")
        if not isinstance(self.foundation_elevation, (int, float)) or isinstance(self.foundation_elevation, bool):
            raise ValueError(f"SurfaceFab {self.name!r} foundation_elevation must be a number")
        if not isinstance(self.leakage, (int, float)) or isinstance(self.leakage, bool):
            raise ValueError(f"SurfaceFab {self.name!r} leakage must be a number")
        if not 0.0 <= self.leakage <= 1.0:
            raise ValueError(f"SurfaceFab {self.name!r} leakage must be within [0, 1]")


def build_default_valley() -> tuple[SurfaceFab, ...]:
    """Return the five valley fabs above Main Strike, each coupled to a chamber.

    Foundation elevations and leakages are fixed model parameters chosen so the
    default flood scenario disables a meaningful share of capacity (the flood's
    urban blast-reach) — validated by tests, not trusted by hand.
    """
    return (
        SurfaceFab("intel_fab", 800.0, "gallery_north", 78.0, 0.85),
        SurfaceFab("amd_fab", 450.0, "gallery_east", 73.0, 0.80),
        SurfaceFab("nec_fab", 600.0, "gallery_south", 92.0, 0.75),
        SurfaceFab("zorin_fab", 650.0, "shaft_a", 98.0, 0.30),
        SurfaceFab("silicon_valley_fab", 500.0, "pump_room", 62.0, 0.70),
    )


def chamber_level_at(
    network: flood.MineNetwork,
    result: flood.FloodResult,
    chamber: str,
    t: float,
) -> float:
    """Free-surface elevation (m above datum) of ``chamber`` at time ``t``.

    Recovered as ``elevation + volume(t) / area`` from the flood result,
    sampled at the nearest gridpoint at or below ``t`` (clamped past the
    horizon). Raises ``ValueError`` on unknown chambers or invalid ``t``.
    """
    if chamber not in result.chamber_names:
        raise ValueError(f"unknown chamber {chamber!r}")
    if not isinstance(t, (int, float)) or isinstance(t, bool):
        raise ValueError("t must be a number")
    if t < 0.0:
        raise ValueError("t must be non-negative")
    i = result.chamber_names.index(chamber)
    step = max(0, min(int(math.floor(t / result.params.dt)), len(result.times) - 1))
    volume = float(result.volumes[i, step])
    chamber_obj = _chamber_by_name(network, chamber)
    return float(chamber_obj.elevation + volume / chamber_obj.area)


def _chamber_by_name(network: flood.MineNetwork, name: str) -> flood.Chamber:
    for chamber in network.chambers:
        if chamber.name == name:
            return chamber
    raise ValueError(f"chamber {name!r} not in network")


def fab_water_table(
    network: flood.MineNetwork,
    result: flood.FloodResult,
    fab: SurfaceFab,
    t: float,
) -> float:
    """Water-table elevation (m above datum) at a fab's foundation at time ``t``."""
    level = chamber_level_at(network, result, fab.chamber, t)
    return float(level * fab.leakage)


def fab_inoperable_at(
    network: flood.MineNetwork,
    result: flood.FloodResult,
    fab: SurfaceFab,
) -> float | None:
    """Earliest time (s) the fab becomes inoperable, or None if it never does
    within the simulated horizon."""
    for step in range(len(result.times)):
        t = float(result.times[step])
        table = fab_water_table(network, result, fab, t)
        if table >= fab.foundation_elevation:
            return t
    return None


def valley_capacity_loss(
    network: flood.MineNetwork,
    result: flood.FloodResult,
    fabs: Iterable[SurfaceFab],
    t: float,
) -> float:
    """Fraction of total fabricating capacity inoperable by time ``t``.

    In the 0..1 range; a fab fully above its foundation at ``t`` is unaffected.
    """
    fab_list = list(fabs)
    if not fab_list:
        return 0.0
    total = sum(f.capacity for f in fab_list)
    if total <= 0:
        return 0.0
    lost = 0.0
    for f in fab_list:
        at = fab_inoperable_at(network, result, f)
        if at is not None and at <= t:
            lost += f.capacity
    return float(lost / total)


def valley_report(
    network: flood.MineNetwork,
    result: flood.FloodResult,
    fabs: Iterable[SurfaceFab],
    t: float,
) -> dict[str, Any]:
    """A deterministic impact digest: per-fab status plus aggregate metrics.

    Returns ``fabs`` (name -> ``{inoperable, inoperable_at, water_table}``),
    ``capacity_loss`` (fraction inoperable by ``t``), ``inoperable`` (count),
    and ``total_capacity``.
    """
    fab_list = list(fabs)
    total = sum(f.capacity for f in fab_list)
    per_fab: dict[str, dict[str, object]] = {}
    lost_count = 0
    for f in fab_list:
        at = fab_inoperable_at(network, result, f)
        inoperable = at is not None and at <= t
        if inoperable:
            lost_count += 1
        per_fab[f.name] = {
            "inoperable": inoperable,
            "inoperable_at": at,
            "water_table": fab_water_table(network, result, f, t),
        }
    victims = sorted(name for name, st in per_fab.items() if st["inoperable"])
    survivors = sorted(name for name, st in per_fab.items() if not st["inoperable"])
    return {
        "fabs": per_fab,
        "capacity_loss": valley_capacity_loss(network, result, fab_list, t),
        "inoperable": lost_count,
        "victims": victims,
        "survivors": survivors,
        "total_capacity": float(total),
    }
