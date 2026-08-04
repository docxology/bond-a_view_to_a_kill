---
title: "Manuscript: a_view_to_a_kill (ZORIN)"
type: "manuscript_guide"
version: "0.1.0"
---

# Manuscript directory — ZORIN

This directory holds the manuscript for the ZORIN film package
(*A View to a Kill*, 1985). All metrics in the prose are injected as
`{{TOKEN}}` values computed by `src/a_view_to_a_kill/manuscript_variables.py`
from the pure domain core; **never hand-author a metric number**.

## File roles

| File | Role |
|---|---|
| `00_abstract.md` ... `99_references.md` | Prose sections (resolved/substituted) |
| `config.yaml` | Identity + experiment parameters (source of truth) |
| `references.bib` | Bibliography |
| `SYNTAX.md`, `README.md`, `AGENTS.md` | Guides (not resolved) |
| `preamble.md` | LaTeX preamble (unused in plain render) |
| `layer_contract.yaml` | Layer-boundary contract |

## Token pipeline

1. `scripts/z_generate_manuscript_variables.py` calls
   `generate_variables()` (strict by default; `--allow-draft` relaxes).
2. `resolve_manuscript_tree` copies each `NN_*.md` to `output/manuscript/`,
   substituting tokens and failing on any leftover `{{TOKEN}}`.
3. Figures render to `output/figures/` via `figures/plots.py`.

The live cross-reference test
(`tests/test_manuscript_variables.py::test_every_manuscript_token_is_generated`)
gates token completeness.

## Editing a section

Update the prose and any token in it; regenerate with
`uv run python scripts/z_generate_manuscript_variables.py` and confirm the
token gate and tests pass.
