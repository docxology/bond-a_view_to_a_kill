---
name: a-view-to-a-kill
description: Build/maintain the PROJECT BOND film package a_view_to_a_kill (ZORIN). Use when working inside this package.
---

# a-view-to-a-kill (ZORIN) — in-repo skill

PROJECT BOND film package for *A View to a Kill* (1985), mission codename
ZORIN. Local-only tree under `projects/working/bond/a_view_to_a_kill/` —
never push, no remote.

## When to use

Working inside this package: adding a concept algorithm, touching the mission
provider, regenerating the manuscript/figures, or running its gates.

## What it is

Three pure domain concepts, each deepened with an extra module in phase 4 —
six pure modules total, wrapped in the FROZEN `bond_api.MissionProvider`:

- `chip_supply_chain.py` — microchip supply-chain security graph: HHI,
  betweenness choke points, single-source dependence, cascade failure,
  monopoly share / post-elimination HHI.
- `acquisition.py` (phase 4) — budgeted monopoly acquisition optimizer:
  exhaustive (optimal) vs greedy, scored by HHI or fabrication share.
- `mine_flood.py` — mass-conserving Euler water-ingress simulation; flood
  fraction, flood times, critical ingress.
- `valley_impact.py` (phase 4) — mine-flood to surface-fab damage coupling
  (urban blast-reach; victim/survivor split of valley capacity).
- `race_analytics.py` — speed indices, EWMA ratings, softmax win
  probabilities, signal-detection cover risk, expected value.
- `race_market.py` (phase 4) — betting-market decimal odds under an overround,
  implied probabilities, Kelly staking, cover-bankroll finance.

Only `mission.py` imports `bond_api` (path dependency in `pyproject.toml`);
`manuscript_variables.py` and `figures/` are `bond_api`-free. `scripts/` are
thin CLIs.

## Quick commands

```bash
cd /Users/4d/Documents/GitHub/template/projects/working/bond/a_view_to_a_kill
uv sync --extra dev
uv run python scripts/z_generate_manuscript_variables.py   # tokens + figures -> output/
uv run python scripts/mission_execute.py                    # run the mission
uv run pytest tests/ --cov=src --cov-fail-under=90 -q
uv run ruff check src/ scripts/ tests/ && uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/
```

## Pitfalls (learned here)

- **Don't put markdown tables in `.yaml` files** — the write-file YAML
  validator rejects them. Use real YAML mappings (see `data/claim_ledger.yaml`).
- **Don't write a literal `{{TOKEN}}` in a manuscript `.md`** — it trips the
  strict cross-reference gate. Write "variable tokens" in prose instead.
- **`bond_api` only in `mission.py`** — the pure core must stay importable
  without it (fallback). Tests verify this shape indirectly.
- **mypy loop-variable collision**: `for i, x in enumerate(xs)` reusing a
  variable name already typed elsewhere in the same function confuses mypy —
  use distinct names (`tunnel_index`, not `pair`).
- **The token cross-ref test strips `{{ }}`** before comparing to
  `generate_variables()` keys — bare names vs braced matches.
- **Coverage gate is total ≥90%** — a ~0% figure file dragged the total under;
  add a `test_figures.py` that renders into `tmp_path` and asserts PNG magic
  bytes + determinism.

## Verification before done

Run the gates above, confirm `rg "template[_]code_project"` is clean (expect
zero in src/manuscript/docs), and `git status` clean after a path-scoped
commit. Record modules + coverage + commit SHA in the final report.
