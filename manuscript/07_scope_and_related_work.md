# Scope and Related Work

## Scope

This package models the *structure* of ZORIN's scheme, not its implementation
in the physical world. The supply chain is a stylized capacity graph, the
mine flood a simplified head-driven weir model, and the race cover a
signal-detection abstraction of stewards' scrutiny. The datasets are fixed,
documented model parameters (historical-company names for the supply chain,
fictionalized gallery geometry for the mine, a reconstructed race card) —
they are illustrative model inputs, not measured field data. No claim is made
about the real historical microchip market's exact shares; the value of the
package is the deterministic, reusable mathematics.

## Related work

- **Concentration and choke points.** The Herfindahl-Hirschman index is the
  standard antitrust concentration measure. Betweenness centrality follows
  Brandes' algorithm. Supply-chain cascades relate to critical-infrastructure
  disruption literature that models how upstream failures starve downstream
  production.
- **Network water flow.** The weir/head-driven flow law used here is a
  simplification of the open-channel flow models used in flood and mine
  drainage engineering; the key property preserved is exact mass conservation.
- **Racing form and detection.** Normalized speed handicapping and softmax
  race models are standard in racing analytics; framing manipulation as a
  signal-detection trade-off draws on statistical detection theory.

Within the PROJECT BOND suite, this package is one of the film packages
implementing the FROZEN `bond_api.MissionProvider` protocol; its pure core
constitutes the local scientific content that the protocol wraps.
