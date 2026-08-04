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

## The three concepts

- **Supply-chain security graph.** Microchips flowed through a multi-stage
  market in 1985 — silicon wafer suppliers, fabrication fabs, assembly and
  packaging houses, and distributors. ZORIN's monopoly is the classic
  choke-point problem: which few firms, if acquired or eliminated, corner the
  market. We formalize this with capacity market shares, the
  Herfindahl-Hirschman concentration index, betweenness centrality, and a
  supply-cascade failure model.
- **Flood-the-mine dynamics.** A mine is a network of chambers and tunnels;
  a sabotage flood is water entering that network and propagating downhill
  under a head-driven flow law. We simulate the water-ingress dynamics
  deterministically and verify exact mass conservation.
- **Race-form cover analytics.** The cover is a horse whose form he can
  knowingly improve. We score legitimate form from raw race records, convert
  ratings to win probabilities, and model the risk that the manipulation is
  detected — a signal-detection trade-off between a bigger win probability
  and a higher chance of being caught.

All mathematics is deterministic (no random draws), all data is fixed and
documented as model parameters, and every result surface — figures,
manuscript tokens, and mission outcomes — is computed from the same pure
core.

## Reader's guide

`src/a_view_to_a_kill/chip_supply_chain.py`,
`src/a_view_to_a_kill/mine_flood.py`, and
`src/a_view_to_a_kill/race_analytics.py` are the mathematical core.
`src/a_view_to_a_kill/mission.py` adapts them to the BOND-API contract;
`src/a_view_to_a_kill/manuscript_variables.py` computes the manuscript
variable tokens that fill this document. Section [@sec:methods] develops the three
models; Section [@sec:results] reports their measured outputs.
