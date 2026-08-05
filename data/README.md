# data/ — ZORIN

`claim_ledger.yaml` registers sourced claims and their **provenance** —
generators and manuscript token names. It deliberately records no numeric
values: a frozen numeral in the ledger would be a second, ungated source of
truth for a metric, which is exactly what the package's "every number is a
computed token" guardrail forbids (an earlier version carried ~10 such
numerals, several already stale). `tests/test_claim_ledger.py` enforces both
halves: every named token must resolve in `generate_variables()`, and no
`value:` key may reappear under `model_datasets` or `computed_metrics`.

The datasets live in the pure core modules (`chip_supply_chain.py`,
`mine_flood.py`, `race_analytics.py`, `valley_impact.py`) as fixed model
parameters; the ledger documents where each one comes from so the mathematics
is reproducible and testable.
