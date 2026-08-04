# Reproducibility

## Determinism

Every module is a pure function of fixed data with no random draws and no
wall-clock dependence in its computed outputs. `Provence.seed` is fixed at
1985; the mission outcome's `input_hash` is a SHA-256 of the canonicalized
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
`output/manuscript/`, and the three figures to `output/figures/`. `output/`
is git-ignored (regenerable). The live test count and achieved coverage are
tracked in `docs/_generated/COUNTS.md`.

## Guardrails check

- Test coverage >= 90% line + branch on `src/` (verified by
  `uv run pytest tests/ --cov=src --cov-fail-under=90`).
- Zero mocks: tests use real computation and real data only.
- No `infrastructure.*` imports in `src/`; pure core is importable without
  `bond_api`.
- No leftover template-scaffold lineage strings (`rg` gate clean).
