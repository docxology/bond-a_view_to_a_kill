"""Microchip supply-chain security graph — monopoly choke-point analysis.

ZORIN's scheme in *A View to a Kill* (1985) is to monopolize the silicon
valley microchip market by eliminating his competitors. This module gives
that scheme a rigorous, deterministic footing: it models the 1985
microchip supply chain as a directed graph of firms (wafer suppliers,
fabricators, assemblers/packagers, distributors) linked by supply flow, and
computes the structural choke points a monopolist would target.

It is pure domain logic — no I/O, no randomness, no ``bond_api`` import —
so it can be lifted into any environment and tested on real (deterministic)
data. The dataset below is a documented historical-reconstruction dataset:
company names are real firms active in the mid-1980s semiconductor market;
capacities are model parameters (thousands of packaged units per quarter)
fixed here for reproducibility and annotated as model data in the claim
ledger.

Concepts implemented
--------------------
* ``market_share`` / ``hhi`` — capacity-based market concentration per
  supply-stage (Herfindahl-Hirschman Index, normalized to 0..10000).
* ``betweenness_centrality`` — Brandes' algorithm on the directed graph;
  the structural choke points of the network.
* ``single_source_dependence`` — downstream firms with exactly one upstream
  supplier (a single point of failure for the monopolist to exploit).
* ``cascade_starved`` — remove nodes (acquired-and-neutralized competitors)
  and measure how much of the downstream network loses its supply path.
* ``monopoly_share`` / ``post_elimination_hhi`` — the ZORIN attack model:
  what market share ZORIN controls, and how concentrated the market becomes,
  once every independent competitor is eliminated and selected firms are
  acquired.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Iterable

__all__ = [
    "STAGES",
    "Supplier",
    "SupplyChain",
    "build_default_supply_chain",
    "validate_graph",
    "successors",
    "predecessors",
    "market_share",
    "hhi",
    "betweenness_centrality",
    "single_source_dependence",
    "cascade_starved",
    "monopoly_share",
    "post_elimination_hhi",
    "top_choke_points",
]

#: The supply-chain stages, ordered from raw input to final distribution.
STAGES = ("wafer", "fabrication", "assembly", "distribution")


@dataclass(frozen=True)
class Supplier:
    """A single firm (node) in the supply chain.

    Attributes:
        name: Unique firm identifier.
        stage: One of :data:`STAGES`.
        capacity: Throughput capacity (thousands of units per quarter).
        owner: ``"zorin"`` for ZORIN-controlled nodes, else an independent
            operator name (defaults to ``"independent"``).
    """

    name: str
    stage: str
    capacity: float
    owner: str = "independent"

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Supplier.name must be a non-empty string")
        if self.stage not in STAGES:
            raise ValueError(f"Supplier {self.name!r} has unknown stage {self.stage!r}; expected one of {STAGES}")
        if not isinstance(self.capacity, (int, float)) or isinstance(self.capacity, bool):
            raise ValueError(f"Supplier {self.name!r} capacity must be a number")
        if self.capacity <= 0:
            raise ValueError(f"Supplier {self.name!r} capacity must be positive")
        if not isinstance(self.owner, str) or not self.owner.strip():
            raise ValueError(f"Supplier {self.name!r} owner must be a non-empty string")


@dataclass(frozen=True)
class SupplyChain:
    """A directed supply graph: nodes are :class:`Supplier` firms, edges are
    ``(upstream, downstream)`` supply flows."""

    suppliers: tuple[Supplier, ...]
    links: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        if not isinstance(self.suppliers, tuple) or not self.suppliers:
            raise ValueError("SupplyChain.suppliers must be a non-empty tuple")
        if not isinstance(self.links, tuple):
            raise ValueError("SupplyChain.links must be a tuple")
        validate_graph(self)


def build_default_supply_chain() -> SupplyChain:
    """Return the documented ZORIN-era microchip supply graph.

    Reconstructed mid-1980s semiconductor market: a handful of silicon wafer
    suppliers feed the fabrication fabs, which feed assembly/packaging
    houses, which feed distributors. ZORIN owns one fabrication fab
    (``zorin_fab``) and one assembly operation, intending to acquire the
    remaining independent fabricators to corner the market.
    """
    suppliers = (
        # --- wafer (raw silicon) ---
        Supplier("siltec", "wafer", 900.0, "siltec"),
        Supplier("monsanto_silicon", "wafer", 700.0, "monsanto"),
        Supplier("wacker", "wafer", 500.0, "wacker"),
        # --- fabrication ---
        Supplier("zorin_fab", "fabrication", 650.0, "zorin"),
        Supplier("intel_fab", "fabrication", 800.0, "intel"),
        Supplier("amd_fab", "fabrication", 450.0, "amd"),
        Supplier("nec_fab", "fabrication", 600.0, "nec"),
        # --- assembly / packaging ---
        Supplier("zorin_assembly", "assembly", 550.0, "zorin"),
        Supplier("amkor", "assembly", 700.0, "amkor"),
        Supplier("carsem", "assembly", 300.0, "carsem"),
        # --- distribution ---
        Supplier("hamilton", "distribution", 900.0, "hamilton"),
        Supplier("arrow", "distribution", 650.0, "arrow"),
    )
    links = (
        # wafer -> fabrication
        ("siltec", "zorin_fab"),
        ("siltec", "intel_fab"),
        ("monsanto_silicon", "intel_fab"),
        ("monsanto_silicon", "amd_fab"),
        ("wacker", "nec_fab"),
        ("wacker", "amd_fab"),
        # fabrication -> assembly
        ("zorin_fab", "zorin_assembly"),
        ("zorin_fab", "amkor"),
        ("intel_fab", "amkor"),
        ("intel_fab", "carsem"),
        ("amd_fab", "amkor"),
        ("nec_fab", "carsem"),
        ("nec_fab", "amkor"),
        # assembly -> distribution
        ("zorin_assembly", "hamilton"),
        ("amkor", "hamilton"),
        ("amkor", "arrow"),
        ("carsem", "arrow"),
        ("carsem", "hamilton"),
    )
    return SupplyChain(suppliers=tuple(suppliers), links=tuple(links))


def validate_graph(chain: SupplyChain) -> None:
    """Validate a :class:`SupplyChain` in place, raising ``ValueError`` on
    duplicate names, unknown nodes in links, or self-loops."""
    names = [s.name for s in chain.suppliers]
    if len(set(names)) != len(names):
        raise ValueError("supply chain contains duplicate supplier names")
    node_set = set(names)
    for upstream, downstream in chain.links:
        if upstream == downstream:
            raise ValueError(f"self-loop link on {upstream!r} is not allowed")
        if upstream not in node_set:
            raise ValueError(f"link references unknown upstream supplier {upstream!r}")
        if downstream not in node_set:
            raise ValueError(f"link references unknown downstream supplier {downstream!r}")
        upstream_stage = _stage_of(chain, upstream)
        downstream_stage = _stage_of(chain, downstream)
        if STAGES.index(downstream_stage) <= STAGES.index(upstream_stage):
            raise ValueError(
                f"link {upstream!r}->{downstream!r} does not flow forward through stages "
                f"({upstream_stage!r} -> {downstream_stage!r})"
            )


def _stage_of(chain: SupplyChain, name: str) -> str:
    for supplier in chain.suppliers:
        if supplier.name == name:
            return supplier.stage
    raise ValueError(f"unknown supplier {name!r}")


def successors(chain: SupplyChain) -> dict[str, tuple[str, ...]]:
    """Return ``node -> tuple(downstream nodes)`` adjacency."""
    out: dict[str, list[str]] = {s.name: [] for s in chain.suppliers}
    for upstream, downstream in chain.links:
        out[upstream].append(downstream)
    return {name: tuple(v) for name, v in out.items()}


def predecessors(chain: SupplyChain) -> dict[str, tuple[str, ...]]:
    """Return ``node -> tuple(upstream nodes)`` adjacency."""
    out: dict[str, list[str]] = {s.name: [] for s in chain.suppliers}
    for upstream, downstream in chain.links:
        out[downstream].append(upstream)
    return {name: tuple(v) for name, v in out.items()}


def _capacity_by_name(chain: SupplyChain) -> dict[str, float]:
    return {s.name: s.capacity for s in chain.suppliers}


def market_share(chain: SupplyChain, stage: str | None = None) -> dict[str, float]:
    """Capacity market share per firm: within ``stage`` (or the whole graph
    when ``stage`` is None) the firm's share is its capacity over the total."""
    if stage is not None and stage not in STAGES:
        raise ValueError(f"unknown stage {stage!r}; expected one of {STAGES}")
    caps = _capacity_by_name(chain)
    selected = {s.name: caps[s.name] for s in chain.suppliers if stage is None or s.stage == stage}
    total = sum(selected.values())
    if total <= 0:
        return {}
    return {name: val / total for name, val in selected.items()}


def hhi(chain: SupplyChain, stage: str | None = None) -> float:
    """Herfindahl-Hirschman concentration index (0..10000) over capacity
    shares. Uses the whole graph when ``stage`` is None."""
    shares = list(market_share(chain, stage).values())
    return float(sum(share * share for share in shares) * 10000.0)


def _unweighted_betweenness(node_order: list[str], adj: dict[str, tuple[str, ...]]) -> dict[str, float]:
    """Brandes' betweenness-centrality algorithm on a directed unweighted
    graph. Returns ``node -> betweenness`` (unnormalized)."""
    centrality = {v: 0.0 for v in node_order}
    for source in node_order:
        stack: list[str] = []
        predecessors_lists: dict[str, list[str]] = {v: [] for v in node_order}
        num_shortest = {v: 0 for v in node_order}
        num_shortest[source] = 1
        distance = {v: -1 for v in node_order}
        distance[source] = 0
        queue: deque[str] = deque([source])
        while queue:
            node = queue.popleft()
            stack.append(node)
            for neighbor in adj[node]:
                if distance[neighbor] < 0:
                    queue.append(neighbor)
                    distance[neighbor] = distance[node] + 1
                if distance[neighbor] == distance[node] + 1:
                    num_shortest[neighbor] += num_shortest[node]
                    predecessors_lists[neighbor].append(node)
        dependency = {v: 0.0 for v in node_order}
        while stack:
            node = stack.pop()
            for predecessor in predecessors_lists[node]:
                dependency[predecessor] += (num_shortest[predecessor] / num_shortest[node]) * (1.0 + dependency[node])
            if node != source:
                centrality[node] += dependency[node]
    return centrality


def betweenness_centrality(chain: SupplyChain) -> dict[str, float]:
    """Betweenness centrality for every firm on the directed supply graph,
    normalized by the number of ordered node pairs (so it lies in 0..1)."""
    node_order = [s.name for s in chain.suppliers]
    adj = successors(chain)
    raw = _unweighted_betweenness(node_order, adj)
    n = len(node_order)
    if n <= 2:
        denominator = 1.0
    else:
        # number of ordered (source, target) pairs, excluding self, for which
        # through-paths are counted twice (directed normalization).
        denominator = max(1.0, float((n - 1) * (n - 2)))
    return {name: (value / denominator) if denominator else 0.0 for name, value in raw.items()}


def single_source_dependence(chain: SupplyChain) -> dict[str, tuple[str, ...]]:
    """Return ``downstream_firm -> upstream suppliers`` for every firm with
    exactly one upstream supplier (a supply single point of failure)."""
    pred = predecessors(chain)
    result: dict[str, tuple[str, ...]] = {}
    for name in pred:
        ups = pred[name]
        if ups and len(ups) == 1:
            result[name] = ups
    return result


def cascade_starved(
    chain: SupplyChain,
    removed: Iterable[str],
) -> tuple[set[str], float]:
    """Simulate the removal of ``removed`` nodes and return
    ``(starved_firms, starved_fraction)``.

    A downstream firm is *starved* when, after removal, it has no directed
    supply path from any surviving wafer supplier. Fraction is starved firms
    over all firms.
    """
    removed_set = set(removed)
    if not removed_set:
        return set(), 0.0
    node_order = [s.name for s in chain.suppliers]
    alive = set(node_order) - removed_set
    adj = successors(chain)
    sources = {s.name for s in chain.suppliers if s.stage == "wafer"} - removed_set
    reached: set[str] = set()
    queue: deque[str] = deque(sources)
    while queue:
        node = queue.popleft()
        if node in reached:
            continue
        reached.add(node)
        for neighbor in adj[node]:
            if neighbor in alive and neighbor not in reached:
                queue.append(neighbor)
    starved = set(node_order) - reached - removed_set
    fraction = len(starved) / len(node_order) if node_order else 0.0
    return starved, float(fraction)


def _zorin_owned(chain: SupplyChain) -> set[str]:
    return {s.name for s in chain.suppliers if s.owner == "zorin"}


def monopoly_share(chain: SupplyChain, acquired: Iterable[str] = ()) -> dict[str, float]:
    """ZORIN's capacity market share per supply stage once every independent
    competitor is eliminated and ``acquired`` firms are absorbed as ZORIN's.

    Every firm not ZORIN-owned and not in ``acquired`` is removed from the
    market; ZORIN's share is his surviving capacity over the surviving
    market within each stage. Stages where ZORIN holds none are reported as
    ``0.0``.
    """
    acquired_set = set(acquired)
    names = {s.name for s in chain.suppliers}
    unknown = acquired_set - names
    if unknown:
        raise ValueError(f"acquired firms unknown: {sorted(unknown)}")
    zorin = _zorin_owned(chain) | acquired_set
    caps = _capacity_by_name(chain)
    out: dict[str, float] = {}
    for stage in STAGES:
        stage_caps = {s.name: caps[s.name] for s in chain.suppliers if s.stage == stage}
        surviving = {name for name in stage_caps if name in zorin}
        total = sum(stage_caps.values())
        if total <= 0:
            out[stage] = 0.0
        else:
            out[stage] = float(sum(caps[name] for name in surviving) / total)
    return out


def post_elimination_hhi(chain: SupplyChain, acquired: Iterable[str] = ()) -> float:
    """Market-wide HHI after the ZORIN elimination attack.

    Independent competitors are removed (starve the market); acquired firms
    are merged into a single ZORIN entity. The resulting HHI measures how
    close to a monopoly the attack brings the whole supply chain.
    """
    acquired_set = set(acquired)
    zorin = _zorin_owned(chain) | acquired_set
    caps = _capacity_by_name(chain)
    merged: dict[str, float] = {}
    for s in chain.suppliers:
        caps_val = caps[s.name]
        if s.name in zorin:
            merged["zorin"] = merged.get("zorin", 0.0) + caps_val
        else:
            merged[s.name] = caps_val
    total = sum(merged.values())
    if total <= 0:
        return 0.0
    return float(sum((v / total) ** 2 for v in merged.values()) * 10000.0)


def top_choke_points(chain: SupplyChain, k: int = 3) -> list[tuple[str, float]]:
    """Return the top-``k`` firms by betweenness centrality as
    ``(name, betweenness)`` pairs, highest first."""
    if not isinstance(k, int) or isinstance(k, bool) or k < 1:
        raise ValueError("k must be a positive integer")
    centrality = betweenness_centrality(chain)
    ranked = sorted(centrality.items(), key=lambda item: (-item[1], item[0]))
    return ranked[:k]
