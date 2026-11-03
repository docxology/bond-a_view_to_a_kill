# src/ — six deterministic models, one adapter, and the metrics the prose reads

`src/a_view_to_a_kill/` (mission codename ZORIN). The package formalizes the film's scheme as six
deterministic computational models and wraps them in the frozen `bond_api.MissionProvider`.

| Module | What it models |
| --- | --- |
| `chip_supply_chain.py` | Capacity graph → market |
| `acquisition.py` | Budgeted monopoly selection: exhaustive optimum against a deterministic greedy, scored by HHI or fabrication share |
| `mine_flood.py` | Mass-conserving, head-driven Euler water |
| `valley_impact.py` | The flood → surface-fab damage coupling |
| `race_analytics.py` | Speed indices → EWMA ratings → race cover |
| `race_market.py` | The market side of the race |
| `metrics.py` | The computed metrics every downstream layer reads |
| `mission.py` | The `bond_api` adapter — the only module that speaks the frozen protocol |
| `manuscript_variables.py`, `figures/` | The token and figure layers |

## Rules

- **`manuscript_variables.py` and `figures/` depend on `metrics.py`, never on `mission.py`.** The
  adapter is a boundary; prose and plots that read through it would be reading the protocol rather than
  the result.
- **Metrics are computed, never authored.** A number typed into a token or a figure is a second answer
  to the same question, and the wrong one the moment the model changes.
- **The six model modules are a pure core: mathematics only.** No `bond_api`, no `infrastructure`, no
  I/O, no RNG, no wall clock — which is what makes byte-identical reruns possible and lets the core
  import on its own.
- **Every model is deterministic**, and the figures are deterministic plots: same inputs, same bytes.
  The claim covers the whole persisted `output/` tree (JSON payload, resolved manuscript sections and
  figures) for an unchanged source tree on one pinned interpreter, and `test_regeneration_determinism.py`
  checks it by running the real generator twice.
- **The adaptation is additive.** The frozen cross-package surface (`MissionProvider`, the mission
  shapes, the `bond_api` protocol) is consumed by the CLI, the coordinator and the other film packages
  — deepen inside it, never rename or re-shape it.
- **`docs/architecture.md` governs module placement** and `docs/agent_instructions.md` governs edits;
  read both before moving code between modules here.
- **Type hints and docstrings throughout**; the gate is ≥90% line and branch coverage on this tree.
