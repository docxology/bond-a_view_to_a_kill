# a_view_to_a_kill — AGENTS.md (ZORIN)

**A PROJECT BOND film package (local-only working tree — never push).**
Mission codename **ZORIN** from *A View to a Kill* (1985). This package
formalizes ZORIN's scheme as deterministic computational models and implements
the FROZEN `bond_api.MissionProvider` protocol.

## Layer contract

| Surface | Rule |
|---|---|
| `src/a_view_to_a_kill/chip_supply_chain.py`, `mine_flood.py`, `race_analytics.py` (pure core) | All mathematics; **no** `bond_api`, **no** `infrastructure`, no I/O, no RNG; importable standalone |
| `src/a_view_to_a_kill/mission.py` | The **only** `bond_api` importer; FROZEN `MissionProvider` + `GadgetRegistry` |
| `src/a_view_to_a_kill/manuscript_variables.py`, `figures/` | `bond_api`-free; metrics computed, never authored; deterministic plots |
| `scripts/` | Thin CLIs (bootstrap + print); no business logic |

Enforced by `uv run pytest tests/ --cov=src --cov-fail-under=90` and
`docs/agent_instructions.md` (read it first).

## Concepts

- **Chip supply chain** (`chip_supply_chain.py`): capacity graph → market
  share / HHI, betweenness choke points, single-source dependence, cascade
  failure, monopoly share + post-elimination HHI.
- **Mine flood** (`mine_flood.py`): mass-conserving head-driven Euler water
  ingress → flood fraction, flood times, critical ingress.
- **Race cover** (`race_analytics.py`): speed indices → EWMA ratings →
  softmax win probabilities → signal-detection cover risk + expected value.

## Usage

```bash
uv sync --extra dev
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run python scripts/z_generate_manuscript_variables.py
```

## Guardrails

- ≥90% line+branch coverage on `src/` (live: `docs/_generated/COUNTS.md`).
- Zero mocks; real computation and real data only.
- Deterministic: fixed datasets, mission seed 1985, byte-identical reruns.
- `bond_api` only in `mission.py` (pure core works in the fallback).
- No leftover template-scaffold lineage strings (verification `rg` gate uses
  a bracket-split pattern so this doc cannot trip its own gate).
- ruff clean, mypy clean, `git status` clean after a path-scoped commit.

See also `docs/agent_instructions.md`, `docs/architecture.md`,
`docs/testing_philosophy.md`, `manuscript/AGENTS.md`, `TODO.md`.
