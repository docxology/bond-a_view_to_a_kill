# scripts/ — Thin Mission CLIs (ZORIN)

Each script self-bootstraps `src/` onto `sys.path` (so `python scripts/x.py`
works from the package root), imports the mission provider, and prints a
report. Thin by contract: no business logic, no math.

| Script | Phase | Prints |
|---|---|---|
| `mission_brief.py` | brief | objectives, assets, constraints |
| `mission_recon.py` | recon | findings for a goal (argv[0] or default) |
| `mission_plan.py` | plan | the four execute steps |
| `mission_execute.py` | execute | computed chip / flood / race metrics + provenance |
| `mission_debrief.py` | debrief | full flow + lessons |
| `z_generate_manuscript_variables.py` | render | tokens + figures to `output/` |

Verification:

```bash
uv run python scripts/mission_brief.py
uv run python scripts/z_generate_manuscript_variables.py
```
