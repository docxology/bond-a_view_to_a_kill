# STANDALONE — a_view_to_a_kill (ZORIN)

This is a PROJECT BOND film package that happens to live inside the template
monorepo's `projects/working/bond/` tree. It is **published**: `origin` is
`docxology/bond-a_view_to_a_kill`, and changes land through an ordinary branch,
pull request and merge.

It started from the template's code-project scaffold and was converted in
phase 1 into a self-contained package with its own git history (own `main`),
a pure domain core importable without `bond_api`, and the FROZEN `bond_api`
`MissionProvider` adapter.

To run it in place:

```bash
cd "$(git rev-parse --show-toplevel)"   # the package root, wherever the checkout lives
uv sync --extra dev
uv run pytest tests/ --cov=src --cov-fail-under=90
```

Lineage note: the original exemplar scaffold is referenced only as historical
lineage; the package no longer depends on it.
