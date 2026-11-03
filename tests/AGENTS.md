# tests/ — zero mocks, and the gates that hold the layers apart

| Suite | Subject |
| --- | --- |
| `test_chip_supply_chain.py`, `test_acquisition.py` | Capacity graph and monopoly selection, with the regret between the exhaustive optimum and the greedy |
| `test_mine_flood.py`, `test_valley_impact.py` | Water ingress, and the flood → fab-damage coupling |
| `test_race_analytics.py`, `test_race_market.py` | Ratings, win probabilities, cover risk; odds, edge, Kelly staking |
| `test_metrics_scenario.py` | Every `experiment:` knob reaches a computed metric |
| `test_claim_ledger.py` | `data/claim_ledger.yaml` records generators and token names, never numerals |
| `test_manuscript_variables.py`, `test_figures.py` | The token and figure layers |
| `test_regeneration_determinism.py` | The determinism claim, by running the real generator twice |
| `test_bond_api_fallback.py` | The pure core with `bond_api` blocked by a real import hook |
| `test_validation_paths.py` | The domain validation paths |
| `test_mission.py`, `test_scripts_smoke.py` | The frozen protocol surface, and the CLIs |

## Rules

- **Zero mocks; real computation and real data only.** `docs/testing_philosophy.md` holds the doctrine
  and the reason: a mock can pass while the mathematics is wrong.
- **The gate is `uv run pytest tests/ --cov=src --cov-fail-under=90`** — 90% floor, line and branch.
- **`test_regeneration_determinism.py` is the determinism claim**, and it is only evidence because it
  runs the real generator twice rather than comparing recorded outputs.
- **`test_bond_api_fallback.py` is the layer gate**: it blocks `bond_api` with a real import hook, so a
  pure-core module that quietly started importing the protocol fails here rather than in a checkout
  where the dependency happens to be present.
- **`test_metrics_scenario.py` fails on a reported-but-unused knob.** A `config.yaml` parameter that is
  only echoed back as a `CONFIG_*` token is a claim the model does not honour.
- **Nothing here hardcodes a metric.** The ledger records generators and token names; a numeral in a
  test that also appears in prose is a second source of truth.
- Run one project test directory per pytest invocation (the house convention), and read
  `docs/testing_philosophy.md` before touching a test file.
