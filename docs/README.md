# Documentation — a_view_to_a_kill (ZORIN)

This directory is the operational rulebook for agents and developers working
inside `a_view_to_a_kill`, the PROJECT BOND film package for *A View to a Kill*
(1985), mission codename **ZORIN**.

## What the package is

ZORIN's scheme in the film has three load-bearing pieces: a **monopoly** over
the microchip supply chain, an **infrastructure sabotage** (flooding the mine
workings under Silicon Valley) that removes his competitors, and a **cover**
operation (a manipulated racehorse) that draws attention and capital away from
the real plan. This package turns each piece into two deterministic, tested
models — one for the structure of the problem, one for the decision that
structure forces — six pure modules in total:

| Piece | Structure | Decision |
|---|---|---|
| Monopoly | `chip_supply_chain.py` — capacity graph, HHI, Brandes betweenness choke points, single-source dependence, cascade failure | `acquisition.py` — budgeted subset selection; exhaustive optimum vs greedy baseline, and the regret between them |
| Sabotage | `mine_flood.py` — mass-conserving head-driven Euler water-ingress simulation over a chamber/tunnel network | `valley_impact.py` — flood-to-surface coupling; water table under each fab, capacity lost, victims vs survivors |
| Cover | `race_analytics.py` — normalized speed indices, EWMA form ratings, softmax win probabilities, signal-detection risk | `race_market.py` — decimal odds under an overround, value edge, Kelly staking, cover-bankroll plan |

`metrics.py` fixes the mission scenario and evaluates all six models into named
metric groups. `mission.py` wraps those groups in the FROZEN
`bond_api.MissionProvider` protocol and is the **only** module that imports
`bond_api`.

## Index of this directory

| File | Read it when |
|---|---|
| [`agent_instructions.md`](agent_instructions.md) | **First.** The behavioral rules governing any change to this package |
| [`architecture.md`](architecture.md) | Before moving code between modules, and to see how `mission.py` implements the frozen protocol |
| [`testing_philosophy.md`](testing_philosophy.md) | Before writing or changing a test |
| [`AGENTS.md`](AGENTS.md) | As the one-screen index of this directory |
| [`_generated/COUNTS.md`](_generated/COUNTS.md) | For the live test count and measured coverage — never hardcode either in prose |

Package-root docs: [`../README.md`](../README.md) (what the package is and how
to run it), [`../AGENTS.md`](../AGENTS.md) (build / test / verify), and
[`../TODO.md`](../TODO.md) (remaining work). The manuscript carries its own
guides at [`../manuscript/README.md`](../manuscript/README.md),
[`../manuscript/AGENTS.md`](../manuscript/AGENTS.md), and
[`../manuscript/SYNTAX.md`](../manuscript/SYNTAX.md).
