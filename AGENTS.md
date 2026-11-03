# a_view_to_a_kill — AGENTS.md (ZORIN)

**A PROJECT BOND film package (published working tree — `origin` is `docxology/bond-a_view_to_a_kill`).**
Mission codename **ZORIN** from *A View to a Kill* (1985). This package
formalizes ZORIN's scheme as six deterministic computational models and
implements the FROZEN `bond_api.MissionProvider` protocol around them.

Read [`docs/agent_instructions.md`](docs/agent_instructions.md) before changing
anything; [`docs/architecture.md`](docs/architecture.md) before moving code
between modules; [`docs/testing_philosophy.md`](docs/testing_philosophy.md)
before touching a test.

## Layer contract

| Surface | Rule |
|---|---|
| `src/a_view_to_a_kill/{chip_supply_chain,acquisition,mine_flood,valley_impact,race_analytics,race_market}.py` (pure core) | All mathematics; **no** `bond_api`, **no** `infrastructure`, no I/O, no RNG, no wall clock |
| `src/a_view_to_a_kill/metrics.py` | `MissionScenario` (the config's knobs) + the six metric groups, each a function of a scenario; protocol-free |
| `src/a_view_to_a_kill/mission.py` | The **only** `bond_api` importer; FROZEN `MissionProvider` + `gadget_registry` |
| `src/a_view_to_a_kill/manuscript_variables.py`, `figures/` | Depend on `metrics.py`, never `mission.py`; metrics computed, never authored; deterministic plots |
| `scripts/` | Thin CLIs (bootstrap `sys.path`, call `src`, print); no business logic |

Enforced by the gates below plus `tests/test_bond_api_fallback.py`, which runs
the pure core with `bond_api` blocked by a real import hook.

## Concepts

- **Chip supply chain** (`chip_supply_chain.py`): capacity graph → market
  share / HHI, betweenness choke points, single-source dependence, cascade
  failure, monopoly share + post-elimination HHI.
- **Acquisition** (`acquisition.py`): budgeted monopoly selection — exhaustive
  optimum vs deterministic greedy, scored by HHI or fabrication share, with
  the regret between them.
- **Mine flood** (`mine_flood.py`): mass-conserving head-driven Euler water
  ingress → flood fraction, flood times, critical ingress, balance audit.
- **Valley impact** (`valley_impact.py`): flood → surface-fab damage coupling
  (water table vs foundation; capacity loss, victims vs survivors).
- **Race cover** (`race_analytics.py`): speed indices → EWMA ratings →
  softmax win probabilities → signal-detection cover risk + expected value.
- **Race market** (`race_market.py`): decimal odds under an overround, value
  edge, Kelly staking, and the cover-bankroll plan.

## Build

```bash
uv sync --extra dev            # deps + the bond-api path dependency
```

## Test

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90        # the gate
uv run pytest tests/test_mission.py -v                    # protocol surface only
uv run pytest tests/test_bond_api_fallback.py -v          # the no-bond-api fallback
```

## Verify (all must pass before a commit)

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/
uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/
uv run python scripts/z_generate_manuscript_variables.py   # tokens must resolve strictly
git status --short                                         # clean after a path-scoped commit
```

## Guardrails

- ≥90% line + branch coverage on `src/` (live value:
  [`docs/_generated/COUNTS.md`](docs/_generated/COUNTS.md) — never hardcode it
  in prose).
- Zero mocks; real computation and real data only.
- Deterministic: fixed datasets, mission seed 1985, no wall clock read
  anywhere, byte-identical reruns. The claim covers the whole persisted
  `output/` tree — JSON payload, resolved manuscript sections, and figures —
  for an unchanged source tree on one pinned interpreter, and it is checked by
  `tests/test_regeneration_determinism.py` running the real generator twice.
- `bond_api` only in `mission.py`; the package resolves it lazily so the pure
  core imports without it.
- The `MissionProvider` surface (`brief`/`recon`/`plan`/`execute`/`debrief`)
  and `gadget_registry` are FROZEN — the fleet consumes them.
- No hand-authored metric in the manuscript; every number is a token. This
  covers `data/claim_ledger.yaml` too — it records generators and token names,
  never numerals (`tests/test_claim_ledger.py`).
- Every `experiment:` knob in `manuscript/config.yaml` must reach a computed
  metric. A knob that is only echoed back as a `CONFIG_*` token is a
  reported-but-unused parameter; `tests/test_metrics_scenario.py` fails on it.
- Scenario-dependent firm names reach the page as tokens, never as literals
  (`test_scenario_acquisition_names_are_never_hand_written_in_prose`).
- No leftover template-scaffold lineage strings (the verification `rg` gate
  uses a bracket-split pattern so this doc cannot trip its own gate).

See also [`README.md`](README.md), [`TODO.md`](TODO.md),
[`docs/`](docs/README.md), and [`manuscript/AGENTS.md`](manuscript/AGENTS.md).
