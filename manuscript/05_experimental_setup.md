# Experimental Setup

All experiments are deterministic and fully prescribed by
`manuscript/config.yaml`, whose `experiment:` block is loaded by
`src/a_view_to_a_kill/manuscript_variables.py`, converted to a
`metrics.MissionScenario`, and threaded into the models that produce every
computed token below. Editing a knob here changes the results, not only the
echo of the file — `tests/test_metrics_scenario.py` fails if any knob is
inert.

## Fixed model data

The datasets are hard-coded, documented model parameters in the pure core and
annotated in `data/claim_ledger.yaml`:

- **Supply chain** (`chip_supply_chain.py`): {{SC_NODES}} firms across the
  stages `{{CORE_STAGES}}` with {{SC_LINKS}}
  forward-flowing supply links; per-firm capacities fixed in the module. The
  acquisition optimizer (`acquisition.py`) derives its candidate set from this
  same graph — the {{ACQ_ACQUIREABLE}} non-ZORIN fabricators — so it adds no
  dataset of its own.
- **Mine network** (`mine_flood.py`): {{FLOOD_CHAMBERS}} chambers with
  volume/area/elevation, {{FLOOD_TUNNELS}} tunnels with cross-sectional area;
  total capacity {{FLOOD_TOTAL_VOLUME}} m$^3$.
- **Valley fabs** (`valley_impact.py`): {{VALLEY_FABS}} surface fabrication
  plants, each with a capacity, a coupled mine chamber, a foundation elevation
  (m above datum), and a hydraulic leakage coefficient in $[0, 1]$.
- **Race card** (`race_analytics.py`): {{RACE_RECORDS}} form records
  ({{RACE_HORSES}} horses x {{RACE_RACES_PER_HORSE}} races) with distance,
  going, weight, and time.
  The betting market (`race_market.py`) is derived from the resulting win
  probabilities under the configured overround — again, no separate dataset.

## Simulation parameters

Scenario knobs come from `manuscript/config.yaml`; structural model constants
(discharge coefficient, Euler timestep, detection threshold, par pace, base
weight, purse, penalty, seed) are defined in the pure modules. Both are
surfaced here as computed tokens, so neither can drift from the code.

- Flood ingress rate: {{CONFIG_FLOOD_INGRESS_RATE}} m$^3$/s, horizon
  {{CONFIG_FLOOD_HORIZON}} s, Euler timestep {{CORE_EULER_DT}} s, discharge
  coefficient {{CORE_DISCHARGE_COEFF}}.
- Race-form EWMA halflife: {{CONFIG_RACE_HALFLIFE}} races.
- Cover boost to Pegasus: {{CONFIG_COVER_BOOST}} speed-index units; natural
  race-to-race variability {{CONFIG_COVER_SIGMA}}; detection threshold
  {{CORE_DETECTION_THRESHOLD}}.
- Acquisition budget: {{CONFIG_ACQUISITION_BUDGET}} independent fabricators.
- Scenario acquisition set (what ZORIN actually buys, distinct from the
  optimizer's answer): `{{SC_SCENARIO_ACQUIRED}}`.
- Cover betting bankroll: {{CONFIG_COVER_BANKROLL}} USD; bookmaker overround
  {{CONFIG_MARKET_OVERROUND}}.
- Mission RNG seed: {{CORE_MISSION_SEED}} (fixed; no randomness is ever drawn).

## Software environment

- Python {{PYTHON_VERSION}}
- numpy, matplotlib, PyYAML; BOND-API protocol via path dependency
- Manuscript source date {{MANUSCRIPT_DATE}}, declared in
  `manuscript/config.yaml`. The generator reads no wall clock, so this line —
  like every other line — is the same on every rerun.
