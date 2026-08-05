# docs/ — Agent-Facing Documentation (ZORIN)

| File | Purpose |
|---|---|
| `agent_instructions.md` | Behavioral rules for AI agents (read-first) |
| `architecture.md` | Module-by-module architecture; pure core / metrics / adapter / scripts boundaries, and how `mission.py` implements the frozen protocol |
| `testing_philosophy.md` | Zero-mock, real-data, deterministic testing doctrine |
| `README.md` | Reader's guide to this directory and to the package's six models |
| `AGENTS.md` | This index |
| `_generated/COUNTS.md` | Live test count + measured coverage (regenerated, never hand-edited) |

Read `agent_instructions.md` first. The rules that bite most often:

1. **≥90% line + branch coverage on `src/`** — a gate, not a target.
2. **All mathematics lives in `src/`**, never in `scripts/`. Scripts bootstrap
   `sys.path`, call `src`, and print.
3. **`bond_api` is imported by `mission.py` only.** Everything else — the six
   concept modules, `metrics.py`, `manuscript_variables.py`, `figures/` — must
   keep working when the path dependency is absent;
   `tests/test_bond_api_fallback.py` enforces that with a real import blocker
   plus a positive control.
4. **Zero mocks.** No `unittest.mock`, `MagicMock`, `@patch`, `create_autospec`.
5. **Full determinism.** Fixed datasets, mission seed 1985, no wall-clock in
   computed outputs.
6. **No hand-authored metric in the manuscript.** Every number is a token from
   `manuscript_variables.py`.
7. **Do not change the public shape of `mission.py`** (`brief` / `recon` /
   `plan` / `execute` / `debrief`) or `gadget_registry` — bond-cli, the
   coordinator reconcile, and the orchestrator consume them across packages.
