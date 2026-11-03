# Live counts — a_view_to_a_kill (ZORIN)

Hand-editing this file is not how it changes: `render_counts_markdown`
in `src/a_view_to_a_kill/manuscript_variables.py` renders it, and
`tests/test_counts_document.py` fails when the file and a fresh render
disagree.

The module and gadget rows are read live off the package, and the test
count is asserted against the suite's own collection, so adding a test
fails the suite until this file is regenerated. The coverage, token,
figure and inventory rows record real runs on
2026-11-03 (the token and figure rows come from
`scripts/z_generate_manuscript_variables.py`) and are not re-derived by
that test: a suite cannot measure its own coverage from inside itself.
The counts were last re-measured in the regeneration-determinism pass
that replaced the wall-clock `GENERATION_TIMESTAMP` with the
config-sourced `MANUSCRIPT_DATE`.

| Metric | Value (measured) |
|---|---|
| Passing tests | 319 |
| Skipped / failed | 0 / 0 |
| Line + branch coverage on `src/` | 100.00% |
| Modules at 100% coverage | all 10: `acquisition`, `chip_supply_chain`, `figures/plots`, `manuscript_variables`, `metrics`, `mine_flood`, `mission`, `race_analytics`, `race_market`, `valley_impact` |
| Lowest-covered module | none — every module at 100% |
| Uncovered statements remaining | 0 (the six unreachable defensive guards were closed with `# pragma: no cover` + rationale; see `TODO.md` Round-2 C1) |
| Pure domain modules | `chip_supply_chain`, `acquisition`, `mine_flood`, `valley_impact`, `race_analytics`, `race_market` |
| Metric layer | `metrics` (six groups: chip / flood / race / acquisition / valley / market) |
| Mission gadgets | `chip_metrics`, `flood_metrics`, `race_metrics`, `acquisition_metrics`, `valley_metrics`, `market_metrics` |
| Manuscript tokens resolved | 87 |
| Figures rendered | 5 |

Re-measure with:

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90 -q
uv run python scripts/z_generate_counts.py --tests <N> --coverage <PCT>
```

Test count alone: `uv run pytest tests/ --collect-only -q | tail -1`.
Token and figure counts: `uv run python scripts/z_generate_manuscript_variables.py`.
