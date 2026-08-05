# TODO — a_view_to_a_kill (ZORIN)

## Phase-4 deep improvement

- **New pure modules**: `acquisition.py` (budgeted monopoly acquisition
  optimizer — exhaustive vs greedy), `valley_impact.py` (mine-flood to
  surface-fab damage coupling, the urban blast-reach), `race_market.py`
  (betting-market odds / Kelly / cover-bankroll finance).
- **Mission deepened inside the protocol**: `mission.py` now reports six
  result groups (chip/flood/race/acquisition/valley/market) and six gadgets;
  plan gains `acquisition`, `valley`, `market` steps. Public protocol surface
  (brief/recon/plan/execute/debrief, `gadget_registry`) unchanged.
- **Manuscript** updated (abstract, methodology, results, setup; new
  `acquisition_curve` + `valley_impact` figures; Kelly/groundwater/supply-chain
  references added to `references.bib`).
- **Coverage raised** to 93.47% on `src/` (186 tests, 0 mocks, 0 failed).

## Built (phase-1 conversion)

- **Pure core**
  - `src/a_view_to_a_kill/chip_supply_chain.py` — microchip supply-chain
    security graph: HHI, betweenness choke points, single-source dependence,
    cascade failure, monopoly share / post-elimination HHI.
  - `src/a_view_to_a_kill/mine_flood.py` — flood-the-mine water-ingress
    dynamics: mass-conserving Euler simulation, flood fraction / times,
    critical ingress, closed-form fill validation.
  - `src/a_view_to_a_kill/race_analytics.py` — race-form cover analytics:
    normalized speed indices, EWMA ratings, softmax win probabilities,
    signal-detection cover risk, expected value.
- **Protocol integration**
  - `src/a_view_to_a_kill/mission.py` — implements the FROZEN
    `bond_api.MissionProvider` (brief/recon/plan/execute/debrief), mission
    seed 1985, and registers mission gadgets on a `GadgetRegistry`.
- **Manuscript & figures**
  - `src/a_view_to_a_kill/manuscript_variables.py` — 59 `{{TOKEN}}` values
    computed from the core (never authored).
  - `src/a_view_to_a_kill/figures/plots.py` — five deterministic PNG figures.
  - `manuscript/` — 8 sections + config.yaml + SYNTAX/AGENTS/README/bib.
- **Scripts** — `mission_brief/recon/plan/execute/debrief.py` +
  `z_generate_manuscript_variables.py` (thin CLIs).
- **Tests** — 186 tests, zero mocks, real data; `--cov=src` at ≥90%
  line+branch (live value in `docs/_generated/COUNTS.md`).

## Declared integration points

- **`bond-api`** (Layer 1): consumed as a path dependency; `mission.py` is the
  only module that imports it. If the path dependency ever fails, the pure
  core and `manuscript_variables.py` remain importable standalone
  (build-your-own-pure-core fallback honored).
- **`bond-utilities` (Q-BRANCH)**: not yet a dependency of this package.
  `mission.py` currently records provenance inline (deterministic
  `Provenance`). Acceptance criteria to adopt the shared helper: delegate
  provenance persistence to `bond_utilities.mission_io.record_provenance_outcome`
  once `bond-utilities` ships as an installable dependency — no rework of the
  pure core required.
- **`bond-orchestrator`** (Layer 3): discovery-ready. The orchestrator finds
  this film by slug `a_view_to_a_kill` on `sys.path` via
  `bond_api.discovery` (`src/a_view_to_a_kill/mission.py` exposes
  `MissionProvider` at module top level). No further wiring required.
