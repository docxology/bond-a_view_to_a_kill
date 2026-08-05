# a_view_to_a_kill — ZORIN

**PROJECT BOND film package · *A View to a Kill* (1985) · mission codename ZORIN**

Special-agent mission software that formalizes Max ZORIN's scheme as
deterministic, fully-tested computational models, wrapped in the FROZEN
`bond_api.MissionProvider` protocol.

## Concepts

1. **Microchip supply-chain monopoly analysis** — `chip_supply_chain.py`
   A directed capacity graph of the mid-1980s semiconductor market. Computes
   market concentration (Herfindahl-Hirschman index), Brandes betweenness
   centrality (structural choke points), single-source dependence, cascade
   failure, and the ZORIN elimination attack (monopoly share +
   post-elimination HHI).
2. **Monopoly acquisition optimizer** — `acquisition.py`
   The budgeted selection problem of which independent fabricators to buy to
   corner the market: exhaustive (optimal) vs greedy search over budget-sized
   subsets, scored by HHI or fabrication share.
3. **Flood-the-mine water-ingress dynamics** — `mine_flood.py`
   A mass-conserving deterministic Euler simulation of water flowing through a
   chamber/tunnel mine network under a head-driven weir law; flood fraction,
   flood times, critical ingress.
4. **Valley impact (urban sabotage)** — `valley_impact.py`
   Couples the flood to the fabs above: rising groundwater disables competitor
   fabrication plants (fraction of capacity lost) while ZORIN's own fab
   survives.
5. **Race-form cover analytics** — `race_analytics.py`
   Normalized speed indices, EWMA form ratings, softmax win probabilities, and
   a signal-detection cover-risk model scoring the trade-off between a bigger
   win probability and the chance the manipulation is detected.
6. **Racing betting-market / cover-finance** — `race_market.py`
   Decimal odds under a bookmaker overround, implied probabilities, the Kelly
   criterion, and a cover-bankroll plan pricing the manipulated horse's edge.

`mission.py` adapts the pure core to the FROZEN `bond_api.MissionProvider`
(brief / recon / plan / execute / debrief) and registers mission gadgets. Only
`mission.py` imports `bond_api` — the pure core is importable standalone.

## Install & run

```bash
uv sync --extra dev            # installs deps + bond-api path dependency
uv run python scripts/mission_execute.py       # compute all mission metrics
uv run python scripts/z_generate_manuscript_variables.py  # tokens + figures
```

## Verify

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ tests/ && uv run ruff format --check src/ scripts/ tests/
uv run mypy src/ scripts/
```

Live test count + coverage: `docs/_generated/COUNTS.md`. The tree is
**local-only** — never push.
