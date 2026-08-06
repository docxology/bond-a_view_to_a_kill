# Results {#sec:results}

All figures and numeric results below are generated from the pure core by
`scripts/z_generate_manuscript_variables.py`; no number is hand-authored.

## Supply-chain monopoly

![Choke-point betweenness by firm](../output/figures/choke_points.png){#fig:choke_points}

Table: Supply-chain concentration under the ZORIN attack.

| Metric | Value |
|---|---|
| Firms / supply links | {{SC_NODES}} / {{SC_LINKS}} |
| Market-wide HHI (pre-attack) | {{SC_HHI_BEFORE}} |
| Market-wide HHI (post-elimination, {{SC_SCENARIO_ACQUIRED_COUNT}} fabs acquired: `{{SC_SCENARIO_ACQUIRED}}`) | {{SC_HHI_AFTER}} |
| ZORIN fabrication capacity share | {{SC_ZORIN_FAB_SHARE}} |
| Top choke point (betweenness) | {{SC_TOP_CHOKE}} |
| Starved fraction when the acquired fabs are dismantled (`{{SC_CASCADE_REMOVED}}`) | {{SC_CASCADE_STARVED}} |

Acquiring `{{SC_SCENARIO_ACQUIRED}}` lifts market concentration from
HHI {{SC_HHI_BEFORE}} to {{SC_HHI_AFTER}} and hands ZORIN
{{SC_ZORIN_FAB_SHARE}} of fabrication capacity — a decisive corner on the
market. The cascade model removes exactly the acquired-and-dismantled firms
(`{{SC_CASCADE_REMOVED}}`); the fabricators left standing
(`{{SC_CASCADE_RETAINED_FABS}}`) still carry wafer supply through to every
assembly house, so nothing downstream is starved (starved fraction
{{SC_CASCADE_STARVED}}, starved firms: {{SC_CASCADE_STARVED_FIRMS}}). That is
the monopolist's intent: competitors are *removed*, but the market ZORIN owns
keeps flowing ([@fig:choke_points]).

## Flood-the-mine water ingress

![Flooded fraction of Main Strike over time](../output/figures/flood_curve.png){#fig:flood_curve}

At ${{CONFIG_FLOOD_INGRESS_RATE}}$ m$^3$/s into the `adit`, the Main Strike
network ({{FLOOD_CHAMBERS}} chambers, {{FLOOD_TUNNELS}} tunnels,
{{FLOOD_TOTAL_VOLUME}} m$^3$) floods ${{FLOOD_FRACTION}}$ of its chambers by
${{CONFIG_FLOOD_HORIZON}}$ s; the lowest working (`vault`) is submerged at
${{FLOOD_VAULT_TIME}}$ s ([@fig:flood_curve]). The critical single ingress
point is `{{FLOOD_CRITICAL_INGRESS}}`. The simulation conserves water mass to
${{FLOOD_WATER_BALANCE}}$ — machine precision.

## Race-form cover analytics

![Race-card form ratings by horse](../output/figures/race_cover.png){#fig:race_cover}

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

![Optimal monopoly HHI by acquisition budget](../output/figures/acquisition_curve.png){#fig:acquisition_curve}

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
acquisitions. Greedy is exact here (regret {{ACQ_REGRET}}) — and this is
*not* a happy accident of this dataset. Both acquisition objectives are
*strategically monotone*: the marginal gain of adding any fabricator is that
fabricator's capacity times a factor common to every candidate, so greedy is
provably optimal on *every* market, not merely this one (a proof sketch and an
exhaustive deterministic counterexample probe live in `test_acquisition.py`).
The exhaustive optimizer's remaining value is as a correctness oracle and as
the upper bound against which the scenario's shortfall is scored; the headline
remains the *scale* of the concentration a {{ACQ_BUDGET}}-firm buy achieves.

### Scenario versus optimizer

The scenario ZORIN actually executes and the answer this package's optimizer
returns are **not the same set**, and the difference is a result, not an
oversight. The film-faithful scenario buys `{{ACQ_SCENARIO_ACQUIRED}}`
({{ACQ_SCENARIO_SIZE}} firms), scoring HHI {{ACQ_SCENARIO_HHI}} and a
fabrication share of {{ACQ_SCENARIO_FAB_SHARE}}. On the same objective and the
same budget, the exhaustive optimum is `{{ACQ_OPTIMAL_ACQUIRED}}` at
{{ACQ_OPTIMAL_HHI}} and a share of {{ACQ_OPTIMAL_FAB_SHARE}}. The scenario is
therefore strictly suboptimal by {{ACQ_SCENARIO_SHORTFALL}} HHI points.

We report this rather than reconcile it away. The package makes **no claim
that ZORIN's acquisition is optimal**; every scenario-conditioned number in
this manuscript (the HHI, share, cascade, and valley results above) is
conditioned on the acquisition set fixed in `manuscript/config.yaml`, not on
the optimizer's answer. The optimizer's role is to bound what the same market
would have permitted — and the bound says the scheme leaves
{{ACQ_SCENARIO_SHORTFALL}} points of concentration on the table.

## Valley impact

![Silicon-valley fabricating capacity lost to the flood](../output/figures/valley_impact.png){#fig:valley_impact}

Table: Urban blast-reach of the flood at the decision horizon.

| Metric | Value |
|---|---|
| Valley fabs | {{VALLEY_FABS}} |
| Capacity loss (fraction inoperable) | {{VALLEY_LOSS}} |
| Inoperable fabs | {{VALLEY_INOPERABLE}} |
| Victims | {{VALLEY_VICTIMS}} |
| Survivors | {{VALLEY_SURVIVORS}} |
| Survivors ZORIN acquires | {{VALLEY_ACQUIRED_SURVIVORS}} |
| Survivors ZORIN neither owns nor acquires | {{VALLEY_UNACQUIRED_SURVIVORS}} |
| Victims ZORIN acquires | {{VALLEY_ACQUIRED_VICTIMS}} |
| Victims ZORIN neither owns nor acquires | {{VALLEY_UNACQUIRED_VICTIMS}} |

By the horizon the flood's groundwater reach has disabled {{VALLEY_INOPERABLE}}
of {{VALLEY_FABS}} valley fabrication plants — {{VALLEY_LOSS}} of total
fabricating capacity ([@fig:valley_impact]) — leaving
{{VALLEY_SURVIVOR_COUNT}} operable: `{{VALLEY_SURVIVORS}}`. ZORIN's own
`zorin_fab` is among them, sitting over the low-coupling `shaft_a` and
protected from the very flood he releases.

The victim list (`{{VALLEY_VICTIMS}}`) is the more interesting result, because
coupling geometry alone decides who drowns. The split by ownership is one-sided.
On the losing side the flood is *not* discriminating: `{{VALLEY_ACQUIRED_VICTIMS}}`
is destroyed even though ZORIN buys it, alongside the plants he never
acquires (`{{VALLEY_UNACQUIRED_VICTIMS}}`). On the surviving side it is
entirely discriminating: the survivors are ZORIN's own plant plus
`{{VALLEY_ACQUIRED_SURVIVORS}}`, which he acquires, and the number of
surviving plants he neither owns nor acquires is
{{VALLEY_UNACQUIRED_SURVIVOR_COUNT}}
(`{{VALLEY_UNACQUIRED_SURVIVORS}}`). So the model contradicts the scheme's own
premise in exactly one direction: the flood spares no rival, but it does
destroy an asset ZORIN pays for — the acquisition plan and the sabotage plan
are not automatically consistent with each other.

Both directions of that claim are computed set operations
(`valley_metrics`), and `tests/test_manuscript_variables.py::test_valley_ownership_split_matches_the_manuscript_claim`
fails if either one stops holding, so this paragraph cannot outlive the data
it describes.

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

The manipulated horse's true probability ({{MARKET_TRUE_PROB}}) exceeds the
market-implied ({{MARKET_IMPLIED}}) by an edge of {{MARKET_EDGE}} per unit
staked, which justifies a Kelly stake of {{MARKET_STAKE}} against the
{{CONFIG_COVER_BANKROLL}} bankroll. Both probabilities come from the *same*
softmax over form ratings — the honest book prices the un-boosted ratings and
the true chance prices the boosted ones — so the edge measures the boost and
nothing else. That a single horse's true chance exceeds the honest market's
price is exactly the statistical anomaly the cover-risk model would flag: the
cover is profitable only while it stays undetectable.
