"""ZORIN mission figures — deterministic matplotlib visualizations.

Renders one figure per concept into ``output/figures/`` using only the
deterministic mission metrics and datasets (no RNG, no external data):

* ``render_choke_points`` — supply-chain choke-point betweenness (bar).
* ``render_flood`` — flooded-fraction-over-time curve for the main strike.
* ``render_cover`` — form ratings and win probability bars for the race card.

``render_mission_figures`` is the orchestrator the manuscript pipeline (and
its thin script) calls. Figures write to an explicit output directory and are
pure functions of their inputs: identical calls produce byte-identical PNGs.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # deterministic, headless-safe backend

import matplotlib.pyplot as plt  # noqa: E402  (backend configured above)

from a_view_to_a_kill import mine_flood as flood
from a_view_to_a_kill import race_analytics as race
from a_view_to_a_kill import mission

__all__ = [
    "render_choke_points",
    "render_flood",
    "render_cover",
    "render_mission_figures",
]


def render_choke_points(out_path: str | Path) -> Path:
    """Bar chart of betweenness centrality per supply-chain firm."""
    chain = mission.chip.build_default_supply_chain()
    centrality = mission.chip.betweenness_centrality(chain)
    names = sorted(centrality, key=lambda n: -centrality[n])
    values = [centrality[n] for n in names]

    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.bar(names, values, color="#7c2d12")
    ax.set_title("Microchip supply-chain choke points (betweenness)")
    ax.set_ylabel("Normalized betweenness")
    ax.set_xlabel("Firm")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    _save(fig, out_path)
    return Path(out_path)


def render_flood(out_path: str | Path) -> Path:
    """Flooded-fraction over time for the default Main Strike scenario."""
    params = mission.FLOOD_PARAMS
    sim = flood.simulate_flood(flood.build_default_mine(), ("adit",), params)
    fractions = [flood.flooded_fraction(sim, t) for t in sim.times]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(sim.times, fractions, color="#0f4c81")
    ax.set_title("Main Strike flood: flooded chambers over time")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Flooded fraction")
    ax.set_ylim(-0.02, 1.02)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    _save(fig, out_path)
    return Path(out_path)


def render_cover(out_path: str | Path) -> Path:
    """Form ratings and win-probability bars for the race card."""
    ratings = race.form_ratings(race.FORM_TABLE)
    names = [name for name, _ in sorted(ratings.items(), key=lambda kv: -kv[1].rating)]
    values = [ratings[n].rating for n in names]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.barh(names, values, color="#1e3a8a")
    ax.set_title("Race-card form ratings (EWMA speed index)")
    ax.set_xlabel("Form rating")
    ax.invert_yaxis()
    fig.tight_layout()
    _save(fig, out_path)
    return Path(out_path)


def render_mission_figures(output_dir: str | Path) -> list[Path]:
    """Render all three concept figures into ``output_dir``; returns paths."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    paths = [
        render_choke_points(out / "choke_points.png"),
        render_flood(out / "flood_curve.png"),
        render_cover(out / "race_cover.png"),
    ]
    plt.close("all")
    return paths


def _save(fig, out_path: str | Path) -> None:
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=120)
    plt.close(fig)
