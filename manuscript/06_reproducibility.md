# Reproducibility

## Determinism

Every module is a pure function of fixed data with no random draws and no
wall-clock dependence in its computed outputs. `Provenance.seed` is fixed at
{{CORE_MISSION_SEED}}; the mission outcome's `input_hash` is a SHA-256 of the canonicalized
plan, so an outcome can be audited without rerunning the film. The flood
simulator is byte-deterministic across identical calls
(`test_mine_flood.py::test_simulation_is_deterministic`), and the mission
report is byte-identical across two `run_mission` calls
(`test_mission.py::test_full_mission_flow_is_deterministic`).

## Artifacts

Running the pipeline reproduces every artifact from source:

```bash
uv run python scripts/mission_brief.py      # brief
uv run python scripts/mission_recon.py      # recon
uv run python scripts/mission_plan.py       # plan
uv run python scripts/mission_execute.py    # execute
uv run python scripts/mission_debrief.py    # debrief
uv run python scripts/z_generate_manuscript_variables.py  # tokens + figures
```

`z_generate_manuscript_variables.py` writes
`output/data/manuscript_variables.json`, the substituted manuscript to
`output/manuscript/`, and the five figures (`choke_points`,
`acquisition_curve`, `flood_curve`, `valley_impact`, `race_cover`) to
`output/figures/`. `output/` is git-ignored (regenerable). The live test count
and achieved coverage are tracked in `docs/_generated/COUNTS.md`.

## Where the numbers come from

No metric in this manuscript is written by hand. Every numeral in the prose,
tables, and captions is a double-brace variable token resolved by
`src/a_view_to_a_kill/manuscript_variables.py`, which reads
`manuscript/config.yaml` for the experiment parameters and calls
`mission.run_mission_metrics()` for the computed results. Two gates keep this
honest:

- `resolve_manuscript_tree(..., strict=True)` refuses to emit a section that
  still contains an unresolved variable token.
- `tests/test_manuscript_variables.py::test_every_manuscript_token_is_generated`
  fails if any token used in prose is missing from `generate_variables()`, and
  `test_strict_gate_rejects_each_empty_metric_group` proves the strict gate
  actually fires when any one metric group is empty.

## Guardrails check

- Test coverage >= 90% line + branch on `src/` (verified by
  `uv run pytest tests/ --cov=src --cov-fail-under=90`).
- Zero mocks: tests use real computation and real data only.
- No `infrastructure.*` imports in `src/`. The pure core, the metric layer,
  the figures, and this manuscript pipeline are importable without `bond_api`
  — verified by `tests/test_bond_api_fallback.py`, which blocks the import
  with a real meta-path finder and recomputes, with a positive control proving
  the blocker bites and a negative control confirming the adapter alone
  requires the protocol.
- No leftover template-scaffold lineage strings (`rg` gate clean).
