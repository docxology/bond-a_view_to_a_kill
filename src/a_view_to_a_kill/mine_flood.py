"""Flood-the-mine infrastructure sabotage model — water-ingress dynamics.

In *A View to a Kill* (1985) ZORIN floods the abandoned mine workings
beneath Silicon Valley to destroy the competing microchip fabrication
plants built above them. This module models that sabotage operation as a
deterministic water-ingress simulation over a mine-gallery network.

Each chamber (node) has a volume, a horizontal cross-sectional area, and an
elevation; each tunnel (edge) connects two chambers with a cross-sectional
area. Water enters at designated ingress points at a total rate ``Q``
(divided evenly among the entries) and propagates through the network under
a simplified weir/orifice flow law:

    q_ij = C * A_tunnel * sqrt(max(h_i - h_j, 0))

where ``h_i = elevation_i + volume_i / area_i`` is the free-surface level of
chamber ``i`` and ``C`` is a discharge coefficient. State evolves by
explicit Euler integration, conserving water mass (the conservation check is
exposed for tests). A chamber is *flooded* once its water level reaches its
full volume.

Pure domain logic — no I/O, no randomness, no ``bond_api`` import. The
default network is a documented reconstruction of "Main Strike", ZORIN's
flooded mine under the valley; gallery volumes and elevations are fixed
model parameters for reproducibility (annotated as model data in the claim
ledger).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable

import numpy as np

__all__ = [
    "Chamber",
    "Tunnel",
    "MineNetwork",
    "FloodParams",
    "FloodResult",
    "build_default_mine",
    "validate_network",
    "ingress_flows",
    "simulate_flood",
    "flooded_fraction",
    "flooded_at",
    "water_balance_error",
    "closed_form_fill_time",
    "critical_ingress",
]

#: Default discharge coefficient of the simplified weir flow law.
DEFAULT_DISCHARGE = 0.6


@dataclass(frozen=True)
class Chamber:
    """A single mine chamber (gallery or shaft)."""

    name: str
    volume: float  # m^3 (full capacity)
    area: float  # m^2 horizontal cross-section -> level = volume / area
    elevation: float  # m above datum

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Chamber.name must be a non-empty string")
        for label, value in (
            ("volume", self.volume),
            ("area", self.area),
            ("elevation", self.elevation),
        ):
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise ValueError(f"Chamber {self.name!r} {label} must be a number")
        if self.volume <= 0:
            raise ValueError(f"Chamber {self.name!r} volume must be positive")
        if self.area <= 0:
            raise ValueError(f"Chamber {self.name!r} area must be positive")


@dataclass(frozen=True)
class Tunnel:
    """A tunnel connecting two chambers."""

    name: str
    a: str  # chamber endpoint
    b: str  # chamber endpoint
    cross_area: float  # m^2 tunnel cross-section

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Tunnel.name must be a non-empty string")
        if not isinstance(self.cross_area, (int, float)) or isinstance(self.cross_area, bool):
            raise ValueError(f"Tunnel {self.name!r} cross_area must be a number")
        if self.cross_area <= 0:
            raise ValueError(f"Tunnel {self.name!r} cross_area must be positive")


@dataclass(frozen=True)
class MineNetwork:
    """A mine: chambers (nodes) connected by bidirectional tunnels (edges)."""

    chambers: tuple[Chamber, ...]
    tunnels: tuple[Tunnel, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.chambers, tuple) or not self.chambers:
            raise ValueError("MineNetwork.chambers must be a non-empty tuple")
        if not isinstance(self.tunnels, tuple):
            raise ValueError("MineNetwork.tunnels must be a tuple")
        validate_network(self)


@dataclass(frozen=True)
class FloodParams:
    """Simulation parameters for :func:`simulate_flood`."""

    ingress_rate: float  # total m^3/s injected into the entries
    horizon: float  # seconds to simulate
    dt: float = 1.0  # Euler timestep, seconds
    discharge: float = DEFAULT_DISCHARGE  # weir coefficient C

    def __post_init__(self) -> None:
        for label, value in (
            ("ingress_rate", self.ingress_rate),
            ("horizon", self.horizon),
            ("dt", self.dt),
            ("discharge", self.discharge),
        ):
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise ValueError(f"FloodParams.{label} must be a number")
        if self.ingress_rate <= 0:
            raise ValueError("FloodParams.ingress_rate must be positive")
        if self.horizon <= 0:
            raise ValueError("FloodParams.horizon must be positive")
        if self.dt <= 0:
            raise ValueError("FloodParams.dt must be positive")
        if self.discharge <= 0:
            raise ValueError("FloodParams.discharge must be positive")


@dataclass(frozen=True)
class FloodResult:
    """The simulated water-ingress time series.

    Attributes:
        chamber_names: Ordered chamber names (index-aligns with ``volumes``).
        full_volumes: Full capacity (m^3) of each chamber, index-aligned
            with ``chamber_names`` — the flood targets for
            :func:`flooded_fraction` / :func:`flooded_at`.
        times: Time grid, length ``n_steps + 1``.
        volumes: ``(n_chambers, n_steps + 1)`` water volume per chamber.
        params: The parameters the simulation ran under.
    """

    chamber_names: tuple[str, ...]
    full_volumes: np.ndarray
    times: np.ndarray
    volumes: np.ndarray
    params: FloodParams


def build_default_mine() -> MineNetwork:
    """Return the documented "Main Strike" mine network beneath the valley.

    Chambers descend from the entrance adit through shafts and galleries to
    the lowest working (the vault). Volumes/elevations are fixed model
    parameters (fictionalized from the film's flooded mine) chosen so a
    modest ingress floods the lower workings within the simulation horizon.
    """
    chambers = (
        Chamber("adit", volume=900.0, area=45.0, elevation=120.0),
        Chamber("shaft_a", volume=1100.0, area=30.0, elevation=95.0),
        Chamber("shaft_b", volume=800.0, area=25.0, elevation=90.0),
        Chamber("gallery_north", volume=1400.0, area=60.0, elevation=70.0),
        Chamber("gallery_east", volume=1200.0, area=55.0, elevation=68.0),
        Chamber("gallery_south", volume=1300.0, area=58.0, elevation=66.0),
        Chamber("pump_room", volume=600.0, area=28.0, elevation=55.0),
        Chamber("vault", volume=1800.0, area=72.0, elevation=40.0),
    )
    tunnels = (
        Tunnel("t_adit_a", "adit", "shaft_a", cross_area=4.0),
        Tunnel("t_adit_b", "adit", "shaft_b", cross_area=3.0),
        Tunnel("t_a_north", "shaft_a", "gallery_north", cross_area=3.5),
        Tunnel("t_b_east", "shaft_b", "gallery_east", cross_area=2.5),
        Tunnel("t_b_south", "shaft_b", "gallery_south", cross_area=2.5),
        Tunnel("t_north_pump", "gallery_north", "pump_room", cross_area=2.0),
        Tunnel("t_east_pump", "gallery_east", "pump_room", cross_area=2.0),
        Tunnel("t_south_pump", "gallery_south", "pump_room", cross_area=2.0),
        Tunnel("t_pump_vault", "pump_room", "vault", cross_area=3.0),
        Tunnel("t_north_east", "gallery_north", "gallery_east", cross_area=1.5),
    )
    return MineNetwork(chambers=tuple(chambers), tunnels=tuple(tunnels))


def validate_network(network: MineNetwork) -> None:
    """Validate a :class:`MineNetwork` in place, raising ``ValueError`` on
    duplicate names, unknown tunnel endpoints, or duplicate tunnels."""
    names = [c.name for c in network.chambers]
    if len(set(names)) != len(names):
        raise ValueError("mine network contains duplicate chamber names")
    node_set = set(names)
    tunnel_names = [t.name for t in network.tunnels]
    if len(set(tunnel_names)) != len(tunnel_names):
        raise ValueError("mine network contains duplicate tunnel names")
    for tunnel in network.tunnels:
        if tunnel.a not in node_set or tunnel.b not in node_set:
            raise ValueError(f"tunnel {tunnel.name!r} references unknown chamber ({tunnel.a!r}, {tunnel.b!r})")
        if tunnel.a == tunnel.b:
            raise ValueError(f"tunnel {tunnel.name!r} is a self-loop")
    seen: set[tuple[str, str]] = set()
    for tunnel in network.tunnels:
        pair: tuple[str, str] = (tunnel.a, tunnel.b) if tunnel.a <= tunnel.b else (tunnel.b, tunnel.a)
        if pair in seen:
            raise ValueError(f"duplicate tunnel between {tunnel.a!r} and {tunnel.b!r}")
        seen.add(pair)


def ingress_flows(
    network: MineNetwork,
    entries: Iterable[str],
    params: FloodParams,
) -> dict[str, float]:
    """Split the total ingress rate equally among the entry chambers.

    Returns ``chamber -> m^3/s``. Raises ``ValueError`` on unknown chambers
    or empty entries.
    """
    entry_list = list(entries)
    if not entry_list:
        raise ValueError("entries must not be empty")
    names = {c.name for c in network.chambers}
    unknown = set(entry_list) - names
    if unknown:
        raise ValueError(f"unknown ingress chambers: {sorted(unknown)}")
    per_entry = params.ingress_rate / len(entry_list)
    return {name: per_entry for name in entry_list}


@dataclass(frozen=True)
class _TunnelPair:
    i: int
    j: int
    cross: float
    name: str


def simulate_flood(
    network: MineNetwork,
    entries: Iterable[str],
    params: FloodParams,
) -> FloodResult:
    """Run the deterministic water-ingress simulation.

    Args:
        network: The mine to flood.
        entries: Chamber names receiving water (rate split evenly).
        params: Ingress rate, horizon, timestep, discharge coefficient.

    Returns:
        A :class:`FloodResult` with the per-chamber volume time series.
    """
    names = [c.name for c in network.chambers]
    index = {name: i for i, name in enumerate(names)}
    areas = np.array([c.area for c in network.chambers], dtype=float)
    volumes = np.array([c.volume for c in network.chambers], dtype=float)
    elevations = np.array([c.elevation for c in network.chambers], dtype=float)

    inflows = ingress_flows(network, entries, params)
    ingress_vector = np.zeros(len(names), dtype=float)
    for name, rate in inflows.items():
        ingress_vector[index[name]] = rate

    tunnels = [_TunnelPair(index[t.a], index[t.b], t.cross_area, t.name) for t in network.tunnels]

    n_steps = int(math.ceil(params.horizon / params.dt))
    times = np.linspace(0.0, params.horizon, n_steps + 1)
    state = np.zeros((len(names), n_steps + 1), dtype=float)
    current = np.zeros(len(names), dtype=float)
    state[:, 0] = current

    for step in range(n_steps):
        levels = elevations + current / areas
        # Tentative weir flows, source -> sink by head difference.
        flows: dict[int, float] = {}  # tunnel index -> tentative q (m^3/s)
        tone: dict[int, int] = {}  # tunnel index -> source chamber
        for pair_index, pair in enumerate(tunnels):
            head = levels[pair.i] - levels[pair.j]
            if head > 0.0:
                flows[pair_index] = params.discharge * pair.cross * math.sqrt(head)
                tone[pair_index] = pair.i
            elif head < 0.0:
                flows[pair_index] = params.discharge * pair.cross * math.sqrt(-head)
                tone[pair_index] = pair.j
        # Per-chamber desired total outflow, capped so a chamber never lends
        # more water than it holds in one timestep (exact mass conservation).
        desired_out: dict[int, float] = {}
        for pair_index, q in flows.items():
            source = tone[pair_index]
            desired_out[source] = desired_out.get(source, 0.0) + q
        scale: dict[int, float] = {}
        for source, total_out in desired_out.items():
            scale[source] = min(1.0, current[source] / (params.dt * total_out))
        for tunnel_index, tunnel in enumerate(tunnels):
            if tunnel_index not in flows:
                continue
            source = tone[tunnel_index]
            sink = tunnel.j if source == tunnel.i else tunnel.i
            q_eff = flows[tunnel_index] * scale.get(source, 1.0)
            current[source] -= q_eff * params.dt
            current[sink] += q_eff * params.dt
        current = current + ingress_vector * params.dt
        current = np.maximum(current, 0.0)
        state[:, step + 1] = current

    return FloodResult(
        chamber_names=tuple(names),
        full_volumes=volumes,
        times=times,
        volumes=state,
        params=params,
    )


def flooded_at(result: FloodResult, chamber: str) -> float | None:
    """Return the time (s) at which ``chamber`` first reaches its full
    volume, or None if it never floods within the simulated horizon."""
    if chamber not in result.chamber_names:
        raise ValueError(f"unknown chamber {chamber!r}")
    i = result.chamber_names.index(chamber)
    target = float(result.full_volumes[i])
    for step in range(len(result.times)):
        if result.volumes[i, step] >= target:
            return float(result.times[step])
    return None


def flooded_fraction(result: FloodResult, t: float) -> float:
    """Fraction of chambers fully flooded at time ``t`` (s).

    The reported fraction is taken at the nearest simulation gridpoint at or
    below ``t``; times beyond the horizon clamp to the final state.
    """
    if not isinstance(t, (int, float)) or isinstance(t, bool):
        raise ValueError("t must be a number")
    if t < 0.0:
        raise ValueError("t must be non-negative")
    step = min(int(math.floor(t / result.params.dt)), len(result.times) - 1)
    step = max(step, 0)
    vol = result.volumes[:, step]
    full = result.full_volumes
    if full.size == 0:
        return 0.0  # pragma: no cover - MineNetwork rejects an empty chamber tuple
    return float(np.count_nonzero(vol >= full) / full.size)


def water_balance_error(result: FloodResult) -> float:
    """Relative water-mass conservation error at the final state.

    Compares the integrated ingress ``Q * t_end`` against the total water
    held in all chambers plus what left via any boundary — here the network
    is closed (no outflows), so the error is
    ``|sum(volumes[-1]) - Q*t_end| / (Q*t_end)``.
    """
    total_in = result.params.ingress_rate * result.params.horizon
    if total_in <= 0.0:
        return 0.0  # pragma: no cover - FloodParams requires positive ingress_rate and horizon
    held = float(np.sum(result.volumes[:, -1]))
    return abs(held - total_in) / total_in


def closed_form_fill_time(chamber: Chamber, rate: float) -> float:
    """Closed-form time to fill a single chamber with an ingress ``rate``
    (m^3/s), ignoring inter-chamber flow: ``volume / rate``."""
    if not isinstance(rate, (int, float)) or isinstance(rate, bool):
        raise ValueError("rate must be a number")
    if rate <= 0.0:
        raise ValueError("rate must be positive")
    return float(chamber.volume / rate)


def critical_ingress(
    network: MineNetwork,
    candidates: Iterable[str],
    params: FloodParams,
) -> tuple[str, float]:
    """Choose the single entry chamber (among ``candidates``) that floods the
    largest fraction of the network by ``params.horizon``.

    Each candidate is simulated alone (receiving the full ingress rate) and
    scored on :func:`flooded_fraction` at the horizon; ties resolve to the
    first candidate in order, keeping the result deterministic. Returns
    ``(chamber, fraction)``.
    """
    candidate_list = list(candidates)
    if not candidate_list:
        raise ValueError("candidates must not be empty")
    names = {c.name for c in network.chambers}
    unknown = set(candidate_list) - names
    if unknown:
        raise ValueError(f"unknown ingress candidates: {sorted(unknown)}")
    best_name = candidate_list[0]
    best_fraction = -1.0
    for name in candidate_list:
        sim = simulate_flood(network, (name,), params)
        fraction = flooded_fraction(sim, params.horizon)
        if fraction > best_fraction:
            best_fraction = fraction
            best_name = name
    return best_name, best_fraction
