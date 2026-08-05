# a_view_to_a_kill — ZORIN

**PROJECT BOND film package · *A View to a Kill* (1985) · mission codename ZORIN**

Special-agent mission software that formalizes Max ZORIN's scheme as
deterministic, fully-tested computational models, wrapped in the FROZEN
`bond_api.MissionProvider` protocol.

## The film, as a specification

ZORIN plans to flood the abandoned mine workings under Silicon Valley,
destroying every competing microchip fabrication plant and leaving his own the
sole survivor — financed and camouflaged by a manipulated racehorse. Three
load-bearing pieces, each modelled twice: once as the *structure* of the
problem, once as the *decision* that structure forces.

| Film concept | Structure module | Decision module |
|---|---|---|
| Microchip monopoly | `chip_supply_chain.py` | `acquisition.py` |
| Flooding the mine (urban sabotage) | `mine_flood.py` | `valley_impact.py` |
| The racing cover | `race_analytics.py` | `race_market.py` |

## Modules

| Module | What it computes |
|---|---|
| `chip_supply_chain.py` | Directed capacity graph of the mid-1980s semiconductor market: market shares, Herfindahl-Hirschman index, Brandes betweenness choke points, single-source dependence, cascade starvation, and the ZORIN attack (monopoly share + post-elimination HHI). |
| `acquisition.py` | Budgeted monopoly selection over the independent fabricators: exhaustive optimum with lexicographic tie-breaking, deterministic greedy baseline, and the regret between them. |
| `mine_flood.py` | Mass-conserving head-driven Euler simulation of water ingress through a chamber/tunnel network: flood fraction, per-chamber flood times, critical ingress point, water-balance audit. |
| `valley_impact.py` | Couples the flood to the surface: water table under each fabrication plant, earliest inoperable time, fraction of valley fabricating capacity lost, victim/survivor split. |
| `race_analytics.py` | Race-form cover analytics: going- and weight-corrected speed indices, EWMA form ratings, softmax win probabilities, signal-detection cover risk, expected value of the manipulation. |
| `race_market.py` | Cover finance: decimal odds under a bookmaker overround, implied probability, value edge, Kelly staking, and the full cover-bankroll plan. |
| `metrics.py` | Fixes the mission scenario (seed 1985, flood parameters, acquired firms, cover boost, bankroll) and evaluates the six models into named metric groups. Protocol-free. |
| `mission.py` | The thin BOND-API adapter: the FROZEN `MissionProvider` plus the module-level `gadget_registry`. The **only** module importing `bond_api`. |
| `manuscript_variables.py` | Computes every manuscript token from `manuscript/config.yaml` + the live metric payload, and resolves the manuscript tree in strict mode. |
| `figures/plots.py` | Five deterministic PNG figures: choke points, acquisition curve, flood curve, valley impact, race cover. |

## The MissionProvider surface

`mission.py` exposes the fleet-wide FROZEN contract — bond-cli, the coordinator
reconcile, and the orchestrator all consume it, so its shape does not change:

```python
from a_view_to_a_kill.mission import MissionProvider, gadget_registry

provider = MissionProvider()
brief   = provider.brief()            # -> MissionBrief   (codename, objectives, assets, constraints)
recon   = provider.recon(request)     # -> ReconReport    (findings)
plan    = provider.plan(brief)        # -> MissionPlan    (7 steps)
outcome = provider.execute(plan)      # -> MissionOutcome (results + Provenance(seed=1985, input_hash))
debrief = provider.debrief(outcome)   # -> Debrief        (outcome + lessons)

# any single metric group, without driving the lifecycle:
gadget_registry.lookup("a_view_to_a_kill", "valley_metrics")()
```

`MissionProvider.film == "a_view_to_a_kill"` is the discovery slug. The six
registered gadgets are `chip_metrics`, `flood_metrics`, `race_metrics`,
`acquisition_metrics`, `valley_metrics`, and `market_metrics`.

Only `mission.py` imports `bond_api`, and the package resolves that module
lazily, so the pure core, the figures, and the manuscript pipeline all run when
the `bond-api` path dependency is unavailable — proven by
`tests/test_bond_api_fallback.py`, not merely asserted here.

## Install & run

```bash
uv sync --extra dev                                       # deps + the bond-api path dependency
uv run python scripts/mission_brief.py                    # the five lifecycle CLIs
uv run python scripts/mission_recon.py
uv run python scripts/mission_plan.py
uv run python scripts/mission_execute.py                  # compute all mission metrics
uv run python scripts/mission_debrief.py
uv run python scripts/z_generate_manuscript_variables.py  # tokens + resolved manuscript + figures
```

## Verify

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/ && uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/
```

The gate is ≥90% line + branch coverage on `src/`, zero failures, zero mocks.
The live measured coverage and test count live in
[`docs/_generated/COUNTS.md`](docs/_generated/COUNTS.md) rather than being
quoted here, so this file cannot go stale.

## Documentation

[`docs/README.md`](docs/README.md) indexes the agent-facing rulebook:
[`agent_instructions.md`](docs/agent_instructions.md) (read first),
[`architecture.md`](docs/architecture.md) (module-by-module design and the
frozen protocol), and [`testing_philosophy.md`](docs/testing_philosophy.md).
[`manuscript/`](manuscript/) holds the paper — every number in it is an
injected token, never hand-authored. [`TODO.md`](TODO.md) tracks remaining
work.

The tree is **local-only**: there is no remote, and nothing here is ever
pushed.
