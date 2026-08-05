# Architecture — ZORIN

## Layers

The package is a strict three-layer stack with dependencies pointing inward:

```
pure core (chip_supply_chain, mine_flood, race_analytics)
        ^            ^            ^
        |            |            |
  manuscript_variables   figures     mission.py (adapter -> bond_api)
        |                            ^
        +------------ scripts -------+
```

| Layer | Modules | Rules |
|---|---|---|
| **Pure core** | `chip_supply_chain.py`, `acquisition.py`, `mine_flood.py`, `valley_impact.py`, `race_analytics.py`, `race_market.py` | All mathematics; no `bond_api`, no `infrastructure`, no I/O, no RNG; importable standalone. |
| **Adapter** | `mission.py` | The **only** `bond_api` importer; implements the FROZEN `MissionProvider`; registers gadgets. |
| **Manuscript / figures** | `manuscript_variables.py`, `figures/plots.py` | `bond_api`-free; metrics computed from the core; deterministic matplotlib. |
| **Orchestration** | `scripts/*.py` | Thin CLIs; bootstrap `sys.path`, call `src`, print reports. |

## Concepts

1. **Supply chain** (`chip_supply_chain.py`): directed capacity graph →
   market share / HHI, Brandes betweenness (choke points),
   single-source dependence, cascade failure, ZORIN monopoly share +
   post-elimination HHI.
2. **Acquisition** (`acquisition.py`): budgeted monopoly selection — exhaustive
   (optimal) vs greedy over budget-sized subsets, scored by HHI or fab share.
3. **Mine flood** (`mine_flood.py`): chamber/tunnel network → mass-conserving
   head-driven Euler water-ingress simulation → flood fraction, flood times,
   critical ingress.
4. **Valley impact** (`valley_impact.py`): couples the flood to surface fabs
   (leakage × chamber head vs foundation) → capacity loss + victim/survivor
   split (urban blast-reach).
5. **Race cover** (`race_analytics.py`): raw race records → normalized speed
   indices → EWMA ratings → softmax win probabilities → signal-detection
   cover risk + expected-value.
6. **Race market** (`race_market.py`): decimal odds under an overround,
   implied probabilities, Kelly staking, cover-bankroll finance.

## Dependencies

`bond-api` (FROZEN `MissionProvider` protocol) via a path dependency in
`pyproject.toml`. Only `mission.py` imports it; the pure core works without it
(the fallback the BOND preamble requires).

## Adding an algorithm

Add the math to the corresponding pure module and write a `test_<module>.py`
with real-data vectors. Do not place math in `scripts/`.
