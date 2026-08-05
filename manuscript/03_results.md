# Results {#sec:results}

All figures and numeric results below are generated from the pure core by
`scripts/z_generate_manuscript_variables.py`; no number is hand-authored.

## Supply-chain monopoly

![Choke-point betweenness by firm]({../output/figures/choke_points.png}){#fig:choke_points}

Table: Supply-chain concentration under the ZORIN attack.

| Metric | Value |
|---|---|
| Firms / supply links | {{SC_NODES}} / {{SC_LINKS}} |
| Market-wide HHI (pre-attack) | {{SC_HHI_BEFORE}} |
| Market-wide HHI (post-elimination, 2 fabs acquired) | {{SC_HHI_AFTER}} |
| ZORIN fabrication capacity share | {{SC_ZORIN_FAB_SHARE}} |
| Top choke point (betweenness) | {{SC_TOP_CHOKE}} |
| Starved fraction when independent fabs removed | {{SC_CASCADE_STARVED}} |

Acquiring `amd_fab` and `nec_fab` lifts market concentration from
HHI {{SC_HHI_BEFORE}} to {{SC_HHI_AFTER}} and hands ZORIN
{{SC_ZORIN_FAB_SHARE}} of fabrication capacity — a decisive corner on the
market. Because the surviving (acquired) fabricators still supply the
assembly stage, the cascade starves nothing downstream
(starved fraction {{SC_CASCADE_STARVED}}), exactly the monopolist's intent:
competitors are *removed*, but the market ZORIN owns keeps flowing
([@fig:choke_points]).

## Flood-the-mine water ingress

![Flooded fraction of Main Strike over time]({../output/figures/flood_curve.png}){#fig:flood_curve}

At ${{CONFIG_FLOOD_INGRESS_RATE}}$ m$^3$/s into the `adit`, the Main Strike
network ({{FLOOD_CHAMBERS}} chambers, {{FLOOD_TUNNELS}} tunnels,
{{FLOOD_TOTAL_VOLUME}} m$^3$) floods ${{FLOOD_FRACTION}}$ of its chambers by
${{CONFIG_FLOOD_HORIZON}}$ s; the lowest working (`vault`) is submerged at
${{FLOOD_VAULT_TIME}}$ s ([@fig:flood_curve]). The critical single ingress
point is `{{FLOOD_CRITICAL_INGRESS}}`. The simulation conserves water mass to
${{FLOOD_WATER_BALANCE}}$ — machine precision.

## Race-form cover analytics

![Race-card form ratings by horse]({../output/figures/race_cover.png}){#fig:race_cover}

Over ${{RACE_RECORDS}}$ records (${{RACE_HORSES}}$ horses, ${{CONFIG_RACE_HALFLIFE}}$
halflife), the strongest form is `{{RACE_TOP_HORSE}}`
(form rating {{RACE_TOP_RATING}}); Pegasus opens at win probability
{{RACE_PEGASUS_PROB}} ([@fig:race_cover]). A ${{CONFIG_COVER_BOOST}}$
speed-index boost to Pegasus buys win probability `+{{COVER_WIN_DELTA}}` while
carrying only ${{COVER_DETECTION_RISK}}$ detection risk, for a positive
expected value of ${{COVER_EXPECTED_VALUE}}$ — a sustainable cover. Pushing
the boost toward the detection threshold collapses expected value as the
scheme is caught (see the methodology analysis in Section [@sec:methods]).

## Monopoly acquisition

![Optimal monopoly HHI by acquisition budget]({../output/figures/acquisition_curve.png}){#fig:acquisition_curve}

Table: Acquisition optimizer on the default market (budget {{ACQ_BUDGET}}).

| Metric | Value |
|---|---|
| Acquireable independent fabricators | {{ACQ_ACQUIREABLE}} |
| Baseline HHI (buy nothing) | {{ACQ_BASELINE_HHI}} |
| Optimal acquired | {{ACQ_OPTIMAL_ACQUIRED}} |
| Optimal HHI | {{ACQ_OPTIMAL_HHI}} |
| HHI gain vs baseline | {{ACQ_HHI_GAIN}} |
| Greedy baseline HHI | {{ACQ_GREEDY_HHI}} |
| Greedy regret | {{ACQ_REGRET}} |

The exhaustive optimum ([@fig:acquisition_curve]) lifts concentration from
{{ACQ_BASELINE_HHI}} to {{ACQ_OPTIMAL_HHI}} with just {{ACQ_BUDGET}}
acquisitions; on this graph greedy matches the optimum (regret
{{ACQ_REGRET}}), so the naive strategy is not the failure mode here — the
headline is the *scale* of the concentration a two-firm buy achieves.

## Valley impact

![Silicon-valley fabricating capacity lost to the flood]({../output/figures/valley_impact.png}){#fig:valley_impact}

Table: Urban blast-reach of the flood at the decision horizon.

| Metric | Value |
|---|---|
| Valley fabs | {{VALLEY_FABS}} |
| Capacity loss (fraction inoperable) | {{VALLEY_LOSS}} |
| Inoperable fabs | {{VALLEY_INOPERABLE}} |
| Victims | {{VALLEY_VICTIMS}} |
| Survivors | {{VALLEY_SURVIVORS}} |

By the horizon the flood's groundwater reach has disabled {{VALLEY_INOPERABLE}}
of {{VALLEY_FABS}} valley fabrication plants — {{VALLEY_LOSS}} of total
fabricating capacity ([@fig:valley_impact]) — while
`{{VALLEY_SURVIVORS}}` remain operable. The survivor list is the tell:
ZORIN's own `zorin_fab` sits over the low-coupling `shaft_a`, protected from
the very flood he releases.

## Cover finance

The betting-market model prices the cover against an honest {{CONFIG_MARKET_OVERROUND}}
overround book. Table: cover-bankroll plan for `{{MARKET_HORSE}}`.

| Metric | Value |
|---|---|
| Bankroll | {{CONFIG_COVER_BANKROLL}} |
| Boosted true win probability | {{MARKET_TRUE_PROB}} |
| Market-implied probability | {{MARKET_IMPLIED}} |
| Value edge per unit | {{MARKET_EDGE}} |
| Kelly fraction | {{MARKET_KELLY}} |
| Kelly stake (USD) | {{MARKET_STAKE}} |
| Expected profit (USD) | {{MARKET_PROFIT}} |

The manipulated horse's true probability ({{MARKET_TRUE_PROB}}) sits just
above the market-implied ({{MARKET_IMPLIED}}), a narrow but positive edge
({{MARKET_EDGE}}) that justifies a Kelly stake of {{MARKET_STAKE}}. That a
single horse's true chance so precisely exceeds the honest market's price is
exactly the statistical anomaly the cover-risk model would flag — the cover
is profitable only while it stays undetectable.
