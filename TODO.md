# TODO — a_view_to_a_kill (ZORIN)

Remaining work only. Completed phases are recorded in the git log, not here.
Live test count and coverage: [`docs/_generated/COUNTS.md`](docs/_generated/COUNTS.md).

## Open — unreachable defensive code

Every reachable branch in `src/` is now covered (`tests/test_validation_paths.py`
closes the error paths). Six statements remain uncovered, and each is
**unreachable through the public API** rather than untested. They should be
either deleted or given an explicit `# pragma: no cover` with a rationale —
leaving them uncovered quietly inflates the "missing" column and hides real
gaps behind noise.

- [ ] `chip_supply_chain.py:188` — `_stage_of` raising on an unknown supplier.
      Private helper; `validate_graph` already rejects links to unknown names
      before it can be called with one.
- [ ] `chip_supply_chain.py:220` and `:375` — the `total <= 0` guards in
      `market_share` and `post_elimination_hhi`. `Supplier.__post_init__`
      rejects non-positive capacity and `SupplyChain` rejects an empty supplier
      tuple, so a zero-capacity market cannot be constructed.
- [ ] `mine_flood.py:355` — `full.size == 0` in `flooded_fraction`;
      `MineNetwork` rejects an empty chamber tuple.
- [ ] `mine_flood.py:369` — `total_in <= 0` in `water_balance_error`;
      `FloodParams` requires positive `ingress_rate` and `horizon`.
- [ ] `valley_impact.py:174` — `total <= 0` in `valley_capacity_loss`;
      `SurfaceFab` requires positive capacity, and the empty-list case is
      already handled (and tested) one branch earlier.

## Open — modelling

- [ ] `valley_impact.fab_inoperable_at` scans the flood result step by step
      (`O(steps)` per fab). Fine at the current horizon; if the horizon grows,
      switch to a bisection over the monotone water-table series.
- [ ] `acquisition.optimal_acquisition` is exhaustive (`C(n, K)`), which is
      deliberate — it is the correctness oracle for the greedy baseline. If the
      acquireable set ever grows past a dozen firms, keep the exhaustive path
      for tests and add a branch-and-bound path for production use.
- [ ] The greedy regret is currently zero on the default graph, so the
      exhaustive-vs-greedy comparison is not yet *discriminating* on the
      shipped data. Consider adding a documented second market fixture where
      greedy demonstrably loses, so the regret metric has a non-trivial case.

## Declared integration points

- **`bond-api`** (Layer 1): consumed as a path dependency. `mission.py` is the
  only module that imports it, and the package resolves `mission` lazily
  (PEP 562), so the pure core, figures, and manuscript pipeline all work when
  the dependency is absent. `tests/test_bond_api_fallback.py` pins this with a
  real import blocker plus positive and negative controls.
- **`bond-utilities` (Q-BRANCH)**: not yet a dependency. `mission.py` records
  provenance inline (deterministic `Provenance`). Acceptance criterion for
  adopting the shared helper: delegate provenance persistence to
  `bond_utilities.mission_io.record_provenance_outcome` once `bond-utilities`
  ships as an installable dependency. No rework of the pure core is required.
- **`bond-orchestrator`** (Layer 3): discovery-ready. The orchestrator finds
  this film by slug `a_view_to_a_kill` on `sys.path` via `bond_api.discovery`;
  `src/a_view_to_a_kill/mission.py` exposes `MissionProvider` at module top
  level. No further wiring required.

## Not doing

- Raising the coverage floor above 90% — the BOND preamble fixes it there, and
  a higher local floor would diverge from the fleet.
- Adding a price/valuation model to `acquisition.py`. The budget is a *count*
  of acquisitions by design; a monetary model is a different paper.
