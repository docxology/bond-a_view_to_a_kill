# AI Agent Instructions — a_view_to_a_kill (ZORIN)

## Why this file exists

`a_view_to_a_kill` is a PROJECT BOND film package — mission codename **ZORIN**,
from *A View to a Kill* (1985). It formalizes the film's scheme as six
deterministic computational models (supply-chain graph, acquisition optimizer,
mine-flood dynamics, valley impact, race-form cover risk, cover finance) and
implements the FROZEN `bond_api.MissionProvider` protocol around that pure
core. Deviating from the rules below — introducing a mock, moving math into
`scripts/`, hand-authoring a metric, importing `bond_api` outside `mission.py`,
or re-shaping the protocol surface — defeats the mission and its guardrails.

Read this file before touching any other file in this package.

---

## Rule 0: Scope

Work only inside this package directory. This tree is **local-only** with no
git remote: commit here, never push. Do not edit sibling BOND packages, the
bond suite root, or the template repo from inside this package.

---

## Rule 1: Read the hub first

Reading order is mandatory, not advisory:

| Document | Governs |
|---|---|
| **This file** | All modifications |
| [`architecture.md`](architecture.md) | Any file-boundary change (pure core / metrics / adapter / scripts) and the frozen protocol contract |
| [`testing_philosophy.md`](testing_philosophy.md) | Any test modification |
| [`../manuscript/AGENTS.md`](../manuscript/AGENTS.md) | Any manuscript edit |

---

## Rule 2: Coverage gate — ≥90% on `src/`

The suite spans one test file per pure module (`test_chip_supply_chain.py`,
`test_acquisition.py`, `test_mine_flood.py`, `test_valley_impact.py`,
`test_race_analytics.py`, `test_race_market.py`) plus `test_mission.py`,
`test_bond_api_fallback.py`, `test_manuscript_variables.py`, `test_figures.py`,
and `test_scripts_smoke.py`. Both this project's `pyproject.toml` and the BOND
preamble gate at 90% line + branch. The live test count and measured coverage
live in [`_generated/COUNTS.md`](_generated/COUNTS.md) — do not hardcode either
in prose.

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90 -q
```

If coverage drops, fix the gap — do not delete tests.

---

## Rule 3: The layer boundary — `scripts/` vs `src/`

- The six pure modules (`chip_supply_chain.py`, `acquisition.py`,
  `mine_flood.py`, `valley_impact.py`, `race_analytics.py`, `race_market.py`)
  contain **all** mathematics: no file I/O, no `bond_api`, no `infrastructure`,
  no randomness, no wall clock.
- `metrics.py` holds the mission scenario constants and evaluates the core into
  six named metric groups. It is protocol-free.
- `mission.py` is the **only** module that imports `bond_api`. It adapts the
  metric groups to the FROZEN `MissionProvider` and registers gadgets.
- `manuscript_variables.py` and `figures/plots.py` depend on `metrics.py`,
  never on `mission.py` — that is what keeps the fallback real.
- `scripts/*.py` are thin CLIs: bootstrap `sys.path`, import, print. **No
  business logic.**

The boundary test: if a line in `scripts/` contains the math that determines an
output (a weir flow, an HHI, a softmax, a Kelly fraction), it violates the
boundary.

---

## Rule 4: The protocol surface is FROZEN

`mission.MissionProvider` (`brief` / `recon` / `plan` / `execute` / `debrief`),
the module-level name `MissionProvider`, and the module-level `gadget_registry`
are consumed across the fleet by bond-cli, the coordinator reconcile, and the
orchestrator. Deepen the package **inside** them — new pure modules, richer
metric groups, more gadget entries — but never rename, remove, or change the
signature of any of them. `a_view_to_a_kill.mission` must stay importable both
as an attribute of the package and as a submodule.

---

## Rule 5: Determinism policy

Everything is deterministic. Fixed datasets, mission seed 1985, no untracked
random draws, no wall-clock value in a computed output. Refactors must preserve
byte-determinism: two `run_mission` calls produce identical reports, the flood
simulator is byte-identical across calls, and the figures re-render
byte-for-byte.

---

## Rule 6: Zero-mock policy

No `unittest.mock`, `MagicMock`, `@patch`, or `create_autospec` anywhere in
`tests/`. Tests use real computation and real data only. Where a test must
observe a missing dependency, use a real import hook (see
`test_bond_api_fallback.py`), never a fake module.

---

## Rule 7: Never hand-author a metric

Every number in `manuscript/*.md` arrives as a double-brace token computed by
`manuscript_variables.py` from `manuscript/config.yaml` plus the live metric
payload. This includes structural model constants (discharge coefficient,
detection threshold, par pace, seed) — they are surfaced as `CORE_*` tokens
precisely so prose cannot drift from the code. To add a number: add the key to
`generate_variables()`, reference the token in prose, and the cross-reference
test verifies it.

---

## Verification before done

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90 -q
uv run ruff check src/ scripts/ tests/ && uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/
uv run python scripts/z_generate_manuscript_variables.py   # tokens must resolve strictly
rg -n "template[_]code_project" . --glob '!uv.lock' --glob '!.git/**' --glob '!output/**' || echo Clean
grep -nrE "^(from|import) infrastructure" src/ || echo Clean
grep -rn "unittest.mock\|MagicMock\|mocker\." tests/ || echo "No mocks"
git status --short   # clean after commit
```
