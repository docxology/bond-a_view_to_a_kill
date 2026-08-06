# Live counts — a_view_to_a_kill (ZORIN)

Measured on the current `main` (regeneration-determinism pass: the wall-clock
`GENERATION_TIMESTAMP` replaced by the config-sourced `MANUSCRIPT_DATE`, plus
`tests/test_regeneration_determinism.py`). These numbers drift as the package
evolves; regenerate them after changing tests or coverage, and never hardcode
them in prose elsewhere.

| Metric | Value (measured) |
|---|---|
| Passing tests | 313 |
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
cd /Users/4d/Documents/GitHub/template/projects/working/bond/a_view_to_a_kill
uv run pytest tests/ --cov=src --cov-fail-under=90 -q
```

Test count alone: `uv run pytest tests/ --collect-only -q | tail -1`.
Token and figure counts: `uv run python scripts/z_generate_manuscript_variables.py`.
