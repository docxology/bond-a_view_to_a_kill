# docs/ — Agent-Facing Documentation (ZORIN)

| File | Purpose |
|---|---|
| `agent_instructions.md` | Behavioral rules for AI agents (read-first) |
| `architecture.md` | Layer boundaries: pure core / adapter / scripts |
| `testing_philosophy.md` | Zero-mock, real-data, deterministic testing |
| `AGENTS.md` | This index |
| `README.md` | Reader's guide |
| `_generated/COUNTS.md` | Live test count + coverage |

Read `agent_instructions.md` first. Key rules: ≥90% coverage on `src/`,
math only in `src/` (never `scripts/`), `bond_api` only in `mission.py`, zero
mocks, full determinism.
