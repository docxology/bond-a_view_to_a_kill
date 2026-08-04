# Manuscript syntax cheat-sheet — ZORIN

This is a reference for editing `manuscript/` in this package. Only the
numbered prose sections (`00_*.md` ... `99_*.md`) are rendered/resolved; the
sidecar files here (`SYNTAX.md`, `AGENTS.md`, `README.md`) are guides and are
excluded from the `{{TOKEN}}` cross-reference gate.

## Variable tokens

Tokens are `{{UPPER_SNAKE_CASE}}`, computed by
`src/a_view_to_a_kill/manuscript_variables.py::generate_variables()` and
substituted into every `NN_*.md` by `resolve_manuscript_tree`. **Never write a
metric number in prose** — always reference a token. The full set (identity,
supply-chain, flood, race/cover, environment) is defined in that module; the
live gate in `tests/test_manuscript_variables.py` fails if any `{{TOKEN}}` in a
prose section is missing from `generate_variables()`.

To add a token: add a key to the returned dict, reference it in prose, and the
cross-reference test verifies it.

## Figures

Referenced with Pandoc-crossref syntax:

```markdown
![caption](../output/figures/choke_points.png){#fig:choke_points}
```

then cited in prose as `[@fig:choke_points]` or `@fig:choke_points`.
Generators live in `src/a_view_to_a_kill/figures/plots.py` and render to
`output/figures/`.

| Label | PNG | Concept |
|---|---|---|
| `{#fig:choke_points}` | `output/figures/choke_points.png` | supply-chain betweenness |
| `{#fig:flood_curve}` | `output/figures/flood_curve.png` | flooded fraction over time |
| `{#fig:race_cover}` | `output/figures/race_cover.png` | race-card form ratings |

## Citations & cross-references

- `[@sec:methods]` / `{#sec:methods}` — section cross-references.
- `[@brandes]`-style keys resolve through `references.bib`.
