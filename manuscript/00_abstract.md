# Abstract

**{{ZORIN_FILM}} · mission codename {{ZORIN_CODENAME}}**

This package implements **{{ZORIN_TITLE}}** as a deterministic,
fully-tested special-agent mission model. It operationalizes the film's
central scheme through three pure, infrastructure-free domain modules:

1. **Microchip supply-chain security graph**
   (`src/a_view_to_a_kill/chip_supply_chain.py`) — a directed graph of the
   mid-1980s semiconductor market (${{SC_NODES}}$ firms, ${{SC_LINKS}}$ supply
   links across four stages). ZORIN's monopoly attack is quantified with the
   Herfindahl-Hirschman concentration index, Brandes betweenness centrality
   for structural choke points, single-source-dependence analysis, and a
   cascade-failure model. Acquiring the independent fabricators lifts
   market-wide HHI from ${{SC_HHI_BEFORE}}$ to ${{SC_HHI_AFTER}}$ and gives
   ZORIN ${{SC_ZORIN_FAB_SHARE}}$ of fabrication capacity.
2. **Flood-the-mine water-ingress dynamics**
   (`src/a_view_to_a_kill/mine_flood.py`) — a deterministic Euler simulation
   of water flowing through the {{FLOOD_CHAMBERS}}-chamber, {{FLOOD_TUNNELS}}-tunnel
   "Main Strike" mine (${{FLOOD_TOTAL_VOLUME}}$ m$^3$), with a mass-conserving
   weir flow law. The default scenario floods ${{FLOOD_FRACTION}}$ of the mine
   by ${{CONFIG_FLOOD_HORIZON}}$ s with a water-balance error of
   ${{FLOOD_WATER_BALANCE}}$ (machine precision).
3. **Horse-race form analytics** (`src/a_view_to_a_kill/race_analytics.py`) —
   normalized speed indices, EWMA form ratings, softmax win probabilities, and
   a signal-detection cover-risk model. For a subtle ${{CONFIG_COVER_BOOST}}$
   speed-index boost to Pegasus the expected value is
   ${{COVER_EXPECTED_VALUE}}$ — viable; a blatant boost is caught.

Every metric is computed, not asserted: figures, dashboard-free manuscript
tokens, and the BOND-API mission provider all draw from the same pure core
(seed $1985$, fully deterministic). Keywords: {{CONFIG_KEYWORDS}}.
