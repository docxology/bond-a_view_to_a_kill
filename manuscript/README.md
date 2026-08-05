# Manuscript — ZORIN (A View to a Kill, 1985)

This package's manuscript formalizes Max ZORIN's scheme as six deterministic
computational models, each backed by one pure module under
`src/a_view_to_a_kill/`:

1. Microchip supply-chain monopoly choke-point analysis (`chip_supply_chain`).
2. Budgeted monopoly acquisition optimization (`acquisition`).
3. Flood-the-mine water-ingress dynamics (`mine_flood`).
4. Valley impact — flood-to-surface-fab capacity loss (`valley_impact`).
5. Race-form cover analytics and detection risk (`race_analytics`).
6. Racing betting market and cover finance (`race_market`).

## Sections

| File | Contents |
|---|---|
| `00_abstract.md` | One-paragraph summary of all six models with headline tokens |
| `01_introduction.md` | The film's scheme, the six models, reader's guide |
| `02_methodology.md` | The mathematics of each model (`{#sec:methods}`) |
| `03_results.md` | Measured outputs, five figures, five tables (`{#sec:results}`) |
| `04_conclusion.md` | What the exercise shows and the guardrails it met |
| `05_experimental_setup.md` | Fixed datasets, config parameters, environment |
| `06_reproducibility.md` | Determinism, artifact regeneration, token provenance |
| `07_scope_and_related_work.md` | What is and is not claimed; sources (`{#sec:scope}`) |
| `99_references.md` | Human-readable bibliography, mirroring `references.bib` |

Sidecars (`config.yaml`, `references.bib`, `preamble.md`, `layer_contract.yaml`,
`SYNTAX.md`, `AGENTS.md`, this file) are not token-resolved.

## Numbers

All numbers flow from `config.yaml` + the pure core through
`manuscript_variables.py` — never hand-authored. To render/regenerate:

```bash
uv run python scripts/z_generate_manuscript_variables.py
```

That writes `output/data/manuscript_variables.json`, the resolved sections to
`output/manuscript/`, and the five figures to `output/figures/`.

See `SYNTAX.md` for token/figure syntax and `AGENTS.md` for editing rules.
