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
