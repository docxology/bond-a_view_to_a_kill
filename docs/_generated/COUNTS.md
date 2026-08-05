# Live counts — a_view_to_a_kill (ZORIN)

Measured on the current `main` (phase-4 deep improvement). These numbers
drift as the suite evolves; regenerate them after changing tests or coverage,
never hardcode them in prose.

| Metric | Value (measured) |
|---|---|
| Passing tests | 186 |
| Skipped / failed | 0 / 0 |
| Line + branch coverage on `src/` | 93.47% |
| Pure domain modules | chip_supply_chain, acquisition, mine_flood, valley_impact, race_analytics, race_market |
| Mission gadgets | chip/flood/race/acquisition/valley/market metrics |

Re-measure with:

```bash
cd /Users/4d/Documents/GitHub/template/projects/working/bond/a_view_to_a_kill
uv run pytest tests/ --cov=src --cov-fail-under=90 -q
```

(Count: `uv run pytest tests/ --collect-only -q | tail -1`.)
