# Live counts — a_view_to_a_kill (ZORIN)

Measured on the current `main` (phase-1 conversion). These numbers drift as the
suite evolves; regenerate them after changing tests or coverage, never hardcode
them in prose.

| Metric | Value (measured) |
|---|---|
| Passing tests | 127 |
| Skipped / failed | 0 / 0 |
| Line + branch coverage on `src/` | 92.65% |

Re-measure with:

```bash
cd /Users/4d/Documents/GitHub/template/projects/working/bond/a_view_to_a_kill
uv run pytest tests/ --cov=src --cov-fail-under=90 -q
```

(Count: `uv run pytest tests/ --collect-only -q | tail -1`.)
