# Experimental Setup

All experiments are deterministic and fully prescribed by
`manuscript/config.yaml` (loaded through
`src/a_view_to_a_kill/manuscript_variables.py`).

## Fixed model data

The three datasets are hard-coded, documented model parameters in the pure
core and annotated in `data/claim_ledger.yaml`:

- **Supply chain** (`chip_supply_chain.py`): {{SC_NODES}} firms across four
  stages (wafer, fabrication, assembly, distribution) with {{SC_LINKS}}
  forward-flowing supply links; per-firm capacities fixed in the module.
- **Mine network** (`mine_flood.py`): {{FLOOD_CHAMBERS}} chambers with
  volume/area/elevation, {{FLOOD_TUNNELS}} tunnels with cross-sectional area;
  total capacity {{FLOOD_TOTAL_VOLUME}} m$^3$.
- **Race card** (`race_analytics.py`): {{RACE_RECORDS}} form records
  ({{RACE_HORSES}} horses x 4 races) with distance, going, weight, and time.

## Simulation parameters (from `manuscript/config.yaml`)

- Flood ingress rate: {{CONFIG_FLOOD_INGRESS_RATE}} m$^3$/s, horizon
  {{CONFIG_FLOOD_HORIZON}} s, Euler timestep 1 s, discharge coefficient 0.6.
- Race-form EWMA halflife: {{CONFIG_RACE_HALFLIFE}} races.
- Cover boost to Pegasus: {{CONFIG_COVER_BOOST}} speed-index units; natural
  race-to-race variability {{CONFIG_COVER_SIGMA}}; detection threshold 1.0.
- Mission RNG seed: 1985 (fixed; no randomness is ever drawn).

## Software environment

- Python {{PYTHON_VERSION}}
- numpy, matplotlib, PyYAML; BOND-API protocol via path dependency
- Generated {{GENERATION_TIMESTAMP}} (UTC)
