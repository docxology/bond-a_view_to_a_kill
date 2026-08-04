# AI Agent Instructions — a_view_to_a_kill (ZORIN)

## Why This File Exists

`a_view_to_a_kill` is a PROJECT BOND film package — mission codename **ZORIN**,
from *A View to a Kill* (1985). It formalizes the film's scheme as
deterministic computational models: a microchip supply-chain monopoly graph,
a flood-the-mine water-ingress simulation, and a horse-race form / cover-risk
model. It implements the FROZEN `bond_api.MissionProvider` protocol around a
pure domain core. Deviating from the rules below — introducing a mock, moving
math to `scripts/`, hand-authoring a metric, or breaking the pure-core
boundary — defeats the mission and the guardrails.

Read this file before touching any other file in this package.

---

## Rule 1: Read the Hub First

Reading order is mandatory, not advisory:

| Document | Governs |
|---|---|
| **This file** | All modifications |
| [`architecture.md`](architecture.md) | Any file-boundary change (pure core vs adapter vs scripts) |
| [`testing_philosophy.md`](testing_philosophy.md) | Any test modification |

---

## Rule 2: Coverage Gate — ≥90% on `src/`

The suite spans the three concept test files (`test_chip_supply_chain.py`,
`test_mine_flood.py`, `test_race_analytics.py`), `test_mission.py`,
`test_manuscript_variables.py`, `test_figures.py`, and `test_scripts_smoke.py`.
Both this project's `pyproject.toml` and the BOND preamble gate at 90%.
Live test count + coverage live in [`docs/_generated/COUNTS.md`](
_generated/COUNTS.md) — do not hardcode either in prose.

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90 -q
```

If coverage drops, fix the gap — do not delete tests.

---

## Rule 3: The Thin Orchestrator Boundary — `scripts/` vs `src/`

- The pure core (`chip_supply_chain.py`, `mine_flood.py`,
  `race_analytics.py`) contains all mathematics: no file I/O, no `bond_api`,
  no `infrastructure`, no randomness.
- `mission.py` is the **only** module that imports `bond_api` — it adapts the
  pure core to the FROZEN `MissionProvider` protocol and registers gadgets.
- `manuscript_variables.py` / `figures/` are also `bond_api`-free.
- `scripts/*.py` are thin CLIs: bootstrap `sys.path`, import `src` + `bond_api`,
  print reports. **No business logic.**

The boundary test: if a line in `scripts/` contains the math that determines
an output (a weir flow, an HHI, a softmax), it violates the boundary.

---

## Rule 4: Determinism Policy

Everything is deterministic. Fixed datasets, fixed seeds (mission seed 1985),
no untracked random draws, no wall-clock in computed outputs. Refactorations
must preserve byte-determinism (two `run_mission` calls produce identical
reports; the flood simulator is byte-identical across calls).

---

## Rule 5: Zero-Mock Policy

No `unittest.mock`, `MagicMock`, `@patch`, or `create_autospec` anywhere in
`tests/`. Tests use real computation and real data only. Mock tests can pass
even when the mathematics is wrong — the mission forbids them.

---

## Verification before done

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90 -q
uv run ruff check src/ scripts/ tests/ && uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/
rg -n "template[_]code_project" . --glob '!uv.lock' --glob '!.git/**' --glob '!output/**' || echo Clean
grep -nrE "^(from|import) infrastructure" src/ || echo Clean
git status --short   # clean after commit
```
