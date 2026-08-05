# Scope and Related Work {#sec:scope}

## Scope

This package models the *structure* of ZORIN's scheme, not its implementation
in the physical world. The supply chain is a stylized capacity graph; the
acquisition optimizer is a combinatorial abstraction of a corporate-control
market with no price model; the mine flood is a simplified head-driven weir
model; the valley coupling is a single-coefficient proxy for a groundwater
transport model; the race cover is a signal-detection abstraction of stewards'
scrutiny; and the betting market is an idealized book with a uniform overround
and no liquidity, stake limits, or price impact. The datasets are fixed,
documented model parameters (historical-company names for the supply chain,
fictionalized gallery geometry for the mine, a reconstructed race card) — they
are illustrative model inputs, not measured field data. No claim is made about
the real historical microchip market's exact shares, about any real mine, or
about any real racing jurisdiction; the value of the package is the
deterministic, reusable mathematics, and the fact that every number reported
here is computed by the tested code rather than asserted in prose.

Two limits are worth stating explicitly. First, the acquisition optimizer is
exhaustive over budget-sized subsets — $\binom{n}{K}$ work — which is
tractable at this problem's scale and deliberately chosen: its purpose is to
be the *correct* oracle against which the greedy baseline's regret is
measured, not to scale. Second, the valley coupling is monotone in chamber
head, so it can order which plants fall and when relative to each other, but
its absolute inundation times inherit the weir model's simplifications and
should not be read as an engineering prediction.

## Related work

- **Concentration and choke points.** The Herfindahl-Hirschman index is the
  standard antitrust concentration measure, codified in the U.S. *Horizontal
  Merger Guidelines* [@hhi]. Betweenness centrality follows Brandes' algorithm
  [@brandes]. Supply-chain cascades relate to the supply-chain resilience
  literature, which models how upstream disruption starves downstream
  production [@christopher2004]; the reachability formulation used for the
  cascade is a standard network-flow construction [@ast].
- **Acquisition as combinatorial selection.** Choosing which competitors to
  buy under a budget is subset selection against a set objective. We report
  the exhaustive optimum alongside a greedy baseline precisely because greedy
  heuristics on such objectives carry no general optimality guarantee — the
  measured regret is the interesting quantity, and on this graph it happens to
  be zero.
- **Network water flow.** The weir/head-driven flow law used here is a
  simplification of the open-channel flow models used in flood and mine
  drainage engineering; the key property preserved is exact mass conservation.
- **Groundwater damage to built assets.** Coupling a subsurface water level to
  the operability of structures above follows the groundwater-inundation
  damage literature, which relates elevated water tables to damage in
  foundations and basements [@kreibich2008].
- **Racing form and detection.** Normalized speed handicapping and softmax
  outcome models are standard in racing and sports-outcome analytics
  [@dixon]; framing manipulation as a signal-detection trade-off draws on
  classical detection theory [@greenswets1966].
- **Bet sizing.** The staking rule is the Kelly criterion — the
  expected-log-growth-optimal fraction of a bankroll to stake on a bet with a
  known edge [@kelly1956].

Within the PROJECT BOND suite, this package is one of the film packages
implementing the FROZEN `bond_api.MissionProvider` protocol; its pure core
constitutes the local scientific content that the protocol wraps.
