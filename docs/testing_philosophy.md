# Testing Philosophy — ZORIN (`a_view_to_a_kill`)

## Zero-mock, real-data testing

No mock framework is ever used in this package: no `unittest.mock`, no
`MagicMock`, no `@patch`, no `create_autospec`, no `mocker` fixture. Every
assertion runs the real algorithm on a fixed, documented dataset and checks a
real mathematical property. The reason is narrow and practical: a mock can pass
while the mathematics underneath it is wrong, which is exactly the failure mode
this package exists to rule out.

Where a test needs to observe behavior under a *missing dependency*, it uses a
real mechanism rather than a fake one. `tests/test_bond_api_fallback.py`
installs an ordinary `sys.meta_path` finder in a fresh subprocess that refuses
to resolve `bond_api`, then runs the genuine computation inside that
interpreter. That is a real import hook, not a stand-in for one.

## What a good assertion looks like here

Prefer assertions a wrong implementation cannot satisfy:

- **Closed forms.** A single chamber filling at rate `Q` reaches volume `V` at
  `t = V/Q`; a two-firm 50/50 market has HHI 5000. Compare against the
  arithmetic, not against a previously recorded output.
- **Invariants.** Water mass is conserved to machine precision
  (`water_balance_error`); softmax win probabilities sum to 1; greedy
  acquisition never beats the exhaustive optimum; the greedy plan always spends
  its whole budget.
- **Determinism.** Two identical calls produce equal results — the flood
  simulation, the full mission report, and the rendered figures are all pinned
  this way.
- **Error paths.** Every `ValueError` branch is reached directly with the bad
  input that triggers it: unknown firm, unknown chamber, non-positive halflife,
  budget exceeding the acquireable set, overround ≤ 1, negative probability.

Avoid assertions that are true by construction. Two rules of thumb caught real
weakness in this package. First, a substring check on a formatted number
(`"0." in value`) passes on a hollow `0.000` — parse the value and bound it
instead. Second, a strict-mode gate written as a chain of `and`s can never
fire; state the gate as "any group empty", then test it by degrading **each**
group in turn, with a positive control proving the undegraded payload still
passes.

## Coverage gate

At least 90% line **and** branch coverage on `src/`. This is a gate, not a
target: if it drops, close the gap — never delete the test.

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90 -q
```

The live measured percentage and test count live in
[`_generated/COUNTS.md`](_generated/COUNTS.md). Regenerate them rather than
quoting a number in prose, which goes stale silently.

## Determinism

Everything is deterministic: fixed datasets, mission seed 1985, no random
draws, and no wall-clock value inside any computed output. The one clock-facing
token (`GENERATION_TIMESTAMP`) takes a `now=` override so tests can pin it, and
`Provenance.wall_time_s` is fixed at `0.0` for the same reason — a real
duration would make the mission report non-reproducible.

## Test file inventory

| File | Covers |
|---|---|
| `test_chip_supply_chain.py` | graph validation, shares, HHI, betweenness, single-source dependence, cascade, monopoly attack |
| `test_acquisition.py` | acquireable set, objectives, exhaustive vs greedy, budget bounds, whole-budget invariant, improvement report |
| `test_mine_flood.py` | parameter validation, mass conservation, analytic fill time, flood times/fraction, critical ingress, determinism |
| `test_valley_impact.py` | fab validation, chamber levels, water tables, inoperable times, capacity loss, report shape |
| `test_race_analytics.py` | record validation, speed indices, EWMA ratings, softmax, detection risk, cover viability |
| `test_race_market.py` | odds under overround, implied probability, value edge, Kelly fraction, cover-bankroll plan |
| `test_mission.py` | the frozen BOND-API surface, lifecycle determinism, gadget registry, metric fidelity |
| `test_bond_api_fallback.py` | pure core, metrics, figures, and manuscript pipeline running with `bond_api` blocked — plus positive and negative controls |
| `test_manuscript_variables.py` | config loading, token map, live token cross-reference, strict resolution, strict metric gate |
| `test_figures.py` | five PNG renders and their determinism |
| `test_scripts_smoke.py` | the thin CLIs end-to-end via subprocess, and their artifacts |

## Conventions

- `conftest.py` pins `MPLBACKEND=Agg` and puts `src/` on `sys.path` regardless
  of how pytest is invoked.
- Script tests run the real CLI in a subprocess — never by importing
  `__main__`.
- Tests that write go through `tmp_path`, not the repo tree, with one
  deliberate exception: the strict-token test temporarily appends to a real
  manuscript section and restores it in a `finally` block.
