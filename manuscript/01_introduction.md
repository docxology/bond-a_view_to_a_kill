# Introduction

In *A View to a Kill* (1985), industrialist Max ZORIN plots to flood the
abandoned mine workings beneath California's Silicon Valley, destroying
every competing microchip fabrication plant and leaving his own operation as
the valley's sole surviving manufacturer. His scheme has three load-bearing
pieces: a **monopoly** over the microchip supply chain, an **infrastructure
sabotage** (the flood) that removes the competition, and a **cover**
operation (a winning racehorse) that draws attention and capital away from
the true plan.

This package turns each piece into real, deterministic, testable mathematics.
It is a PROJECT BOND film package: it implements the FROZEN
`bond_api.MissionProvider` protocol (the mission lifecycle of brief, recon,
plan, execute, debrief) around a pure domain core that is deliberately free
of protocol imports, so the science stands alone and the protocol is a thin
adapter.

## The six models

Each of the three load-bearing pieces is developed twice: once as the
*structure* of the problem and once as the *decision* the structure forces.

- **Supply-chain security graph** (`chip_supply_chain.py`). Microchips flowed
  through a multi-stage market in 1985 — silicon wafer suppliers, fabrication
  fabs, assembly and packaging houses, and distributors. ZORIN's monopoly is
  the classic choke-point problem: which few firms, if acquired or eliminated,
  corner the market. We formalize this with capacity market shares, the
  Herfindahl-Hirschman concentration index, betweenness centrality, and a
  supply-cascade failure model.
- **Monopoly acquisition optimizer** (`acquisition.py`). Given the graph, the
  monopoly is a *budgeted selection* problem: with money for $K$ purchases,
  which independent fabricators does ZORIN buy? We solve it exhaustively (the
  optimum, with deterministic tie-breaking) and greedily (the naive baseline),
  and report the regret between them.
- **Flood-the-mine dynamics** (`mine_flood.py`). A mine is a network of
  chambers and tunnels; a sabotage flood is water entering that network and
  propagating downhill under a head-driven flow law. We simulate the
  water-ingress dynamics deterministically and verify exact mass conservation.
- **Valley impact** (`valley_impact.py`). The flood is only the mechanism; the
  sabotage is what it reaches. Each surface fabrication plant is hydraulically
  coupled to a mine chamber, so rising chamber head raises the water table
  under the fab until its foundation is inundated. This converts the flood
  curve into lost fabricating capacity — and shows which plant survives.
- **Race-form cover analytics** (`race_analytics.py`). The cover is a horse
  whose form he can knowingly improve. We score legitimate form from raw race
  records, convert ratings to win probabilities, and model the risk that the
  manipulation is detected — a signal-detection trade-off between a bigger win
  probability and a higher chance of being caught.
- **Cover finance** (`race_market.py`). A cover that cannot be monetized is not
  a cover. We price the manipulated horse against an *honest* bookmaker's book
  under an overround, compute the value edge, and size the position by the
  Kelly criterion — which is also exactly the statistical signature a
  regulator would look for.

All mathematics is deterministic (no random draws), all data is fixed and
documented as model parameters, and every result surface — figures,
manuscript tokens, and mission outcomes — is computed from the same pure
core.

## Reader's guide

`chip_supply_chain.py`, `acquisition.py`, `mine_flood.py`,
`valley_impact.py`, `race_analytics.py`, and `race_market.py` (all under
`src/a_view_to_a_kill/`) are the mathematical core: pure functions with no
protocol imports, no I/O, and no randomness. `mission.py` adapts them to the
BOND-API contract — it is the only module that imports `bond_api`.
`manuscript_variables.py` computes the manuscript variable tokens that fill
this document, and `figures/plots.py` renders the five figures. Section
[@sec:methods] develops all six models; Section [@sec:results] reports their
measured outputs; Section [@sec:scope] states what the models do and do not
claim.
