# Live counts — a_view_to_a_kill (ZORIN)

Measured on the current `main` (phase-5 documentation and defect pass). These
numbers drift as the package evolves; regenerate them after changing tests or
coverage, and never hardcode them in prose elsewhere.

| Metric | Value (measured) |
|---|---|
| Passing tests | 244 |
| Skipped / failed | 0 / 0 |
| Line + branch coverage on `src/` | 99.11% |
| Modules at 100% coverage | `acquisition`, `figures/plots`, `manuscript_variables`, `metrics`, `mission`, `race_analytics`, `race_market` |
| Lowest-covered module | `chip_supply_chain` (97.79%) |
| Uncovered statements remaining | 6 — all unreachable defensive guards, enumerated in `TODO.md` |
| Pure domain modules | `chip_supply_chain`, `acquisition`, `mine_flood`, `valley_impact`, `race_analytics`, `race_market` |
| Metric layer | `metrics` (six groups: chip / flood / race / acquisition / valley / market) |
| Mission gadgets | `chip_metrics`, `flood_metrics`, `race_metrics`, `acquisition_metrics`, `valley_metrics`, `market_metrics` |
| Manuscript tokens resolved | 71 |
| Figures rendered | 5 |

Re-measure with:

```bash
cd /Users/4d/Documents/GitHub/template/projects/working/bond/a_view_to_a_kill
uv run pytest tests/ --cov=src --cov-fail-under=90 -q
```

Test count alone: `uv run pytest tests/ --collect-only -q | tail -1`.
Token and figure counts: `uv run python scripts/z_generate_manuscript_variables.py`.
