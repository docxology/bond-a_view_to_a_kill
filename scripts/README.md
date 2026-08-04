# scripts/ — README

Run any mission phase from the package root:

```bash
uv run python scripts/mission_brief.py
uv run python scripts/mission_recon.py "locate the flooding adit"
uv run python scripts/mission_plan.py
uv run python scripts/mission_execute.py
uv run python scripts/mission_debrief.py
uv run python scripts/z_generate_manuscript_variables.py
```

`z_generate_manuscript_variables.py` is strict by default: it fails if any
`{{TOKEN}}` in the manuscript is unresolved or any metric group is empty.
Pass `--allow-draft` only to relax that gate for early drafts.

See `AGENTS.md` for the phase map.
