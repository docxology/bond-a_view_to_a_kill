# Abstract

**{{ZORIN_FILM}} · mission codename {{ZORIN_CODENAME}}**

This package implements **{{ZORIN_TITLE}}** as a deterministic,
fully-tested special-agent mission model. It operationalizes the film's
central scheme through six pure, infrastructure-free domain modules:

1. **Microchip supply-chain security graph**
   (`chip_supply_chain.py`) — a directed graph of the mid-1980s semiconductor
   market (${{SC_NODES}}$ firms, ${{SC_LINKS}}$ supply links across four
   stages). Concentration (HHI), Brandes betweenness choke points,
   single-source dependence, and cascade failure quantify the monopoly
   attack.
2. **Monopoly acquisition optimizer** (`acquisition.py`) — the budgeted
   selection problem of which independent fabricators ZORIN buys to corner
   the market. Exhaustive search for the optimal acquisition raises
   market-wide HHI from a {{ACQ_BASELINE_HHI}} baseline to
   {{ACQ_OPTIMAL_HHI}} with a budget of {{ACQ_BUDGET}}, a gain of
   {{ACQ_HHI_GAIN}}.
3. **Flood-the-mine water-ingress dynamics** (`mine_flood.py`) — a
   mass-conserving deterministic Euler simulation of water flowing through
   the {{FLOOD_CHAMBERS}}-chamber "Main Strike" network, flooding
   {{FLOOD_FRACTION}} of it by {{CONFIG_FLOOD_HORIZON}} s with a
   water-balance error of ${{FLOOD_WATER_BALANCE}}$ (machine precision).
4. **Valley impact / urban sabotage** (`valley_impact.py`) — couples the
   flood to the fabs above: rising groundwater disables
   {{VALLEY_INOPERABLE}} of {{VALLEY_FABS}} valley fabs, {{VALLEY_LOSS}} of
   fabricating capacity, while ZORIN's own fab (`{{VALLEY_SURVIVORS}}`)
   survives.
5. **Horse-race form analytics** (`race_analytics.py`) — normalized speed
   indices, EWMA ratings, softmax win probabilities, and a
   signal-detection cover-risk model. A subtle {{CONFIG_COVER_BOOST}}
   speed-index boost to Pegasus carries only {{COVER_DETECTION_RISK}}
   detection risk (expected value {{COVER_EXPECTED_VALUE}}); a blatant boost
   is caught.
6. **Racing betting-market / cover-finance** (`race_market.py`) — converts
   win probabilities to honest-market decimal odds under a
   {{CONFIG_MARKET_OVERROUND}} overround, and prices the cover: Pegasus's
   boosted true probability ({{MARKET_TRUE_PROB}}) exceeds the market-implied
   ({{MARKET_IMPLIED}}), yielding a positive value edge ({{MARKET_EDGE}}) and
   a Kelly stake of {{MARKET_STAKE}} — the exact anomaly to detect.

Every metric is computed, not asserted: figures, manuscript tokens, and the
BOND-API mission provider all draw from the same pure core (seed 1985, fully
deterministic). Keywords: {{CONFIG_KEYWORDS}}.
