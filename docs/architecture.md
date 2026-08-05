# Architecture — ZORIN (`a_view_to_a_kill`)

## Dependency stack

Dependencies point strictly downward. Nothing below the adapter line knows the
BOND-API protocol exists.

```
scripts/            mission_brief · mission_recon · mission_plan
  (thin CLIs)       mission_execute · mission_debrief
                    z_generate_manuscript_variables
        |                                   |
        v                                   v
mission.py  ------ (the ONLY bond_api importer; FROZEN MissionProvider) -----+
        |                                                                    |
        v                                                                    |
metrics.py  ------ scenario constants + the six metric groups (pure) --------+
        |                          ^                       ^
        v                          |                       |
+-------------------------+  manuscript_variables.py   figures/plots.py
| PURE CORE (six modules) |  (token hydration)         (5 deterministic PNGs)
| chip_supply_chain       |
| acquisition             |  -> acquisition   depends on chip_supply_chain
| mine_flood              |  -> valley_impact depends on mine_flood
| valley_impact           |  -> race_market   depends on race_analytics
| race_analytics          |
| race_market             |
+-------------------------+
```

| Layer | Modules | Rules |
|---|---|---|
| **Pure core** | `chip_supply_chain.py`, `acquisition.py`, `mine_flood.py`, `valley_impact.py`, `race_analytics.py`, `race_market.py` | All mathematics. No `bond_api`, no `infrastructure`, no file I/O, no RNG, no wall clock. |
| **Metric layer** | `metrics.py` | Fixes the mission scenario and evaluates the core into six named groups. Protocol-free. |
| **Adapter** | `mission.py` | The **only** `bond_api` importer. Implements the FROZEN `MissionProvider`; registers gadgets. |
| **Presentation** | `manuscript_variables.py`, `figures/plots.py` | Depend on `metrics.py`, never on `mission.py`. Deterministic matplotlib (Agg backend). |
| **Orchestration** | `scripts/*.py` | Thin CLIs: bootstrap `sys.path`, call `src`, print. No business logic. |

## Module by module

### `chip_supply_chain.py` — the market as a graph

A directed capacity graph over the stages `wafer -> fabrication -> assembly ->
distribution`; `build_default_supply_chain()` returns the fixed mid-1980s
reconstruction. It computes capacity market shares and the
Herfindahl-Hirschman index (`hhi`), Brandes betweenness centrality and
`top_choke_points`, single-source dependence, `cascade_starved` (which
downstream firms lose all supply-path reachability when a set of firms is
removed), and the ZORIN attack pair `monopoly_share` /
`post_elimination_hhi`.

### `acquisition.py` — which firms to buy

Turns that graph into a budgeted selection problem over the non-ZORIN
fabricators (`acquireable_firms`). `optimal_acquisition` exhaustively scores
every budget-sized subset against an objective (`hhi` or `fab_share`) and
returns the lexicographically smallest maximizer; `greedy_acquisition` is the
deterministic hill-climbing baseline; `improvement` reports the optimum, the
buy-nothing baseline, and the gain. `greedy <= optimal` holds by construction,
so the gap between them is measurable regret rather than an assumption.

### `mine_flood.py` — the sabotage mechanism

A chamber/tunnel network (`build_default_mine()` is "Main Strike"). Water
enters designated ingress chambers and flows tunnel-wise from higher head to
lower under a weir law `q = C·a·sqrt(max(Δh, 0))`, integrated by explicit
Euler. Each step's tentative flows are rescaled so no chamber lends more water
than it holds, which makes the scheme **exactly mass-conserving** —
`water_balance_error` is the audit of that claim. It reports
`flooded_fraction`, `flooded_at`, and `critical_ingress` (the single entry
point that floods the most of the network by the horizon).

### `valley_impact.py` — what the flood reaches

Couples the flood to the surface. A `SurfaceFab` carries a capacity, a coupled
chamber, a foundation elevation, and a leakage coefficient in `[0, 1]`.
`chamber_level_at` recovers a chamber's free-surface elevation from the flood
result; `fab_water_table` scales it by leakage; `fab_inoperable_at` finds the
earliest time that table reaches the foundation; `valley_capacity_loss` and
`valley_report` aggregate to the fraction of fabricating capacity lost plus the
victim/survivor split. This is where ZORIN's own fab surviving becomes a
computed result rather than a plot point.

### `race_analytics.py` — the cover's form

Raw race records normalize to a going- and weight-corrected pace, converted to
a speed index against par. `form_ratings` is the EWMA over a horse's indices;
`win_probabilities` is a softmax over ratings; `manipulated_probabilities`
re-runs it with a boost added to one horse. `detection_risk` is the
signal-detection probability that a boost `b` clears the stewards' threshold
given the standard error of the mean over `n` races, and `cover_viability`
trades win-probability gain against that risk in expected value.

### `race_market.py` — the cover's finance

`market_odds` prices honest decimal odds under a bookmaker overround;
`implied_probability`, `value_edge`, and `kelly_fraction` form the standard
bet-sizing chain; `cover_bankroll` assembles the full `CoverPlan` for the
boosted horse — its boosted true probability against the *un-boosted* market,
the value edge, the Kelly stake capped at the bankroll, and the expected
profit.

### `metrics.py` — the mission scenario

Holds the scenario constants (`SEED`, `FLOOD_PARAMS`, `ACQUIRED_FIRMS`,
`COVER_BOOST`, `COVER_SIGMA`, `ACQUISITION_BUDGET`, `COVER_BANKROLL`,
`PACKAGE_VERSION`) and one function per concept — `chip_metrics`,
`flood_metrics`, `race_metrics`, `acquisition_metrics`, `valley_metrics`,
`market_metrics` — aggregated by `run_mission_metrics()` into the six-group
payload. It imports no protocol types, which is what makes the `bond_api`
fallback real rather than aspirational.

### `manuscript_variables.py` and `figures/plots.py`

`generate_variables()` merges `manuscript/config.yaml` with the live metric
payload into the token map; `resolve_manuscript_tree()` substitutes those
tokens into every `NN_*.md` section and refuses (in strict mode) to emit a file
that still contains an unresolved token. `figures/plots.py` renders five
deterministic PNGs — `choke_points`, `acquisition_curve`, `flood_curve`,
`valley_impact`, `race_cover` — from the same metric layer.

## How `mission.py` implements the frozen `MissionProvider`

`bond_api.protocol.MissionProvider` is a `Protocol`: any class exposing the
five lifecycle methods with the right signatures satisfies it structurally —
there is no base class to inherit. `mission.MissionProvider` is that class, and
the suite discovers it by slug: the orchestrator imports
`a_view_to_a_kill.mission` and binds the top-level name `MissionProvider`. That
name, the five methods, and the module-level `gadget_registry` are FROZEN
across the fleet. Deepen the package *inside* them; never re-shape them.

| Stage | Signature | What this package does |
|---|---|---|
| `brief` | `() -> MissionBrief` | Declares the film and codename ZORIN, the mission objectives, three `Asset`s (supply-chain dataset, mine network, race card), and the `Constraint`s (determinism, no-mocks, scope). |
| `recon` | `(ReconRequest) -> ReconReport` | Returns `Finding`s echoing the request goal plus the shape of each fixed dataset and the determinism constraint. |
| `plan` | `(MissionBrief) -> MissionPlan` | Emits seven `Step`s — `supply_chain`, `acquisition`, `mine_flood`, `valley`, `race_cover`, `market`, `verify` — each carrying its parameters. |
| `execute` | `(MissionPlan) -> MissionOutcome` | Calls `metrics.run_mission_metrics()`, records the completed step names, and attaches `Provenance(package_version, seed=1985, input_hash, wall_time_s=0.0)`. |
| `debrief` | `(MissionOutcome) -> Debrief` | Wraps the outcome with the mission's standing lessons. |

`_input_hash(plan)` is a SHA-256 over the canonical JSON of the plan's steps
(sorted keys, no whitespace), so an outcome is auditable without re-running it.
`wall_time_s` is pinned to `0.0` deliberately: a real duration would break
byte-determinism of the mission report, and determinism is the harder
guarantee to keep.

`gadget_registry` is a `bond_api.registry.GadgetRegistry` holding six
zero-argument callables registered under the film slug (`chip_metrics`,
`flood_metrics`, `race_metrics`, `acquisition_metrics`, `valley_metrics`,
`market_metrics`), so the orchestrator can pull a single metric group without
driving the whole lifecycle.

### Lazy adapter loading

`a_view_to_a_kill/__init__.py` imports the six concept modules and `metrics`
eagerly but resolves `mission` through a PEP 562 module `__getattr__`.
Consumers see no difference — `a_view_to_a_kill.mission` and
`from a_view_to_a_kill import mission` both work, and `dir()` still lists it —
but importing the package, or any pure module through it, no longer drags in
`bond_api`. That is the mechanism behind the fallback these docs promise;
`tests/test_bond_api_fallback.py` proves it with a real import blocker and a
positive control.

## Dependencies

`bond-api` (the FROZEN protocol) via a path dependency declared in
`pyproject.toml` under `[tool.uv.sources]`. Runtime libraries: numpy,
matplotlib, PyYAML.

## Adding an algorithm

1. Put the mathematics in the matching pure module, or in a new pure module
   that imports only other pure modules.
2. Add `tests/test_<module>.py` with real-data vectors and closed-form or
   invariant assertions — see `testing_philosophy.md`.
3. If it produces a reportable number, surface it through a `metrics.py` group
   and a token in `manuscript_variables.py`, then reference the token in the
   manuscript. Never write the number into prose.
4. Do not touch the public shape of `mission.py` or `gadget_registry`.
