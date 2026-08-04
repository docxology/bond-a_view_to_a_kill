# Testing Philosophy — ZORIN

## Zero-mock, real-data testing

No mock framework is ever used. Every assertion runs the real algorithm on a
fixed, documented dataset and checks a real mathematical property — a known
HHI, an analytic fill time, a conservation invariant, a probability that sums
to 1, a deterministic byte-equal rerun. Mocks are forbidden because a mock can
pass while the underlying math is wrong.

## Coverage gate

Target ≥90% line **and** branch on `src/` (live number in
`docs/_generated/COUNTS.md`). Run:

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90 -q
```

## Determinism

Tests prefer analytical inputs and closed-form expectations (e.g. single
chamber fill time `V/Q`, HHI for a two-firm market). Where a simulator runs,
the test asserts conservation and byte-determinism across identical calls.

## Test files / class inventory

| File | Covers |
|---|---|
| `test_chip_supply_chain.py` | graph validity, HHI, betweenness, cascade, monopoly attack |
| `test_mine_flood.py` | validation, conservation, analytic fill, flood time/fraction, critical ingress |
| `test_race_analytics.py` | speed indices, EWMA, softmax, detection risk, cover viability |
| `test_mission.py` | BOND-API protocol, determinism, gadgets, metric fidelity |
| `test_manuscript_variables.py` | config, token map, live `{{TOKEN}}` cross-ref, strict resolution |
| `test_figures.py` | PNG render + determinism |
| `test_scripts_smoke.py` | thin CLIs via subprocess, artifact output |

## Conventions

- `conftest.py` pins `MPLBACKEND=Agg` and adds `src/` to `sys.path`.
- Explicit error-path tests hit `ValueError` branches (unknown names, bad
  params, empty inputs) directly.
- No wall-clock in asserted outputs; the timestamp token is overridable via
  `now=` for deterministic tests.
