# Methodology {#sec:methods}

All six models are pure functions of fixed, documented datasets; no random
draws, no external state, no wall-clock dependence. This guarantees
byte-identical reruns. The three *structural* models come first
(supply-chain graph, flood dynamics, race form); the three *decision* models
that build on them follow (acquisition optimizer over the graph, valley-impact
coupling over the flood, cover finance over the form ratings).

## Implementation layering

The six models live in six independent modules under
`src/a_view_to_a_kill/`. A seventh module, `metrics.py`, fixes the mission
scenario (which firms are acquired, the flood parameters, the cover boost, the
bankroll) and evaluates each model once into a named metric group. `metrics.py`
imports no protocol types, so the entire scientific pipeline — the models, the
metric groups, the figures, and the manuscript token hydration — runs without
`bond_api` installed. `mission.py` is the only module that imports the
protocol; it wraps the same metric groups in the FROZEN `MissionProvider`
lifecycle and registers them as gadgets. Section results are therefore
identical whether reached through the protocol or through the pure core.

## Microchip supply-chain monopoly analysis

The supply chain is a directed graph of firms $V$ (nodes) and supply links
$E \subseteq V \times V$ (edges flowing forward through stages
`{{CORE_STAGES}}`). Each firm $v$ has a
throughput capacity $c_v$. The default dataset is a documented
reconstruction of the mid-1980s semiconductor market (${{SC_NODES}}$ firms,
${{SC_LINKS}}$ links).

**Concentration.** Within a stage (or the whole graph), firm $v$'s capacity
share is $s_v = c_v / \sum_u c_u$, and the Herfindahl-Hirschman index is
$\mathrm{HHI} = 10000 \sum_v s_v^2$, ranging from $0$ (perfect competition)
to $10000$ (monopoly) — the antitrust codification of concentration [@hhi].
The default market opens at HHI ${{SC_HHI_BEFORE}}$.

**Choke points.** Structural choke points are measured with Brandes'
betweenness-centrality algorithm [@brandes]: a firm's betweenness is the fraction of
ordered node pairs for which it lies on a shortest directed supply path.
Wafer sources carry zero betweenness by construction; the top choke point is
`{{SC_TOP_CHOKE}}` (see [@fig:choke_points]).

**Single-source dependence.** A downstream firm whose only upstream supplier
is one firm is a single point of failure; such dependencies are the monopolist's
pressure points.

**Cascade failure.** Removing a set $R$ of firms (acquired-and-dismantled
competitors), a downstream firm is *starved* if it has no directed supply path
from any surviving wafer supplier — a standard reachability construction on
the supply digraph [@ast], and the mechanism the resilience literature calls
upstream disruption propagation [@christopher2004]. The starved fraction is
$\sum_{v \in S} 1 / |V|$. In the reported scenario $R$ is exactly the acquired
set `{{SC_CASCADE_REMOVED}}`; the fabricators that remain in the graph after
that removal are `{{SC_CASCADE_RETAINED_FABS}}`.

**The ZORIN attack.** ZORIN owns `zorin_fab` and `zorin_assembly`; by
acquiring the independent fabricators `{{SC_SCENARIO_ACQUIRED}}` and
eliminating the rest of the market, his fabrication share rises to
${{SC_ZORIN_FAB_SHARE}}$ and market-wide HHI jumps to ${{SC_HHI_AFTER}}$.
Formally, `monopoly_share` computes ZORIN's surviving capacity share per
stage once every non-acquired independent is removed, and
`post_elimination_hhi` merges ZORIN's holdings into one entity before
recomputing concentration. This acquisition set is a *scenario* input
(`manuscript/config.yaml`), not the optimizer's output; Section
[@sec:results] reports how far apart the two are.

## Flood-the-mine water-ingress dynamics

The mine is a network of chambers (nodes) and bidirectional tunnels (edges).
Chamber $i$ has volume $\Omega_i$, horizontal cross-sectional area $A_i$, and
elevation $z_i$; water level is $h_i = z_i + w_i / A_i$ where $w_i$ is the
water volume in the chamber. Tunnels have cross-sectional area $a_{ij}$.

Water enters at designated ingress chambers at total rate $Q$ (split evenly),
and flows through each tunnel from the higher-head end to the lower under a
simplified weir law

$$ q_{ij} = C\, a_{ij}\, \sqrt{\max(h_i - h_j,\, 0)}, $$

with discharge coefficient $C = {{CORE_DISCHARGE_COEFF}}$. Each timestep's tentative flows are
scaled so no chamber lends more water than it holds, making the scheme
**exactly mass-conserving**. State evolves by explicit Euler with timestep
${{CORE_EULER_DT}}$ s to horizon ${{CONFIG_FLOOD_HORIZON}}$ s at ingress
${{CONFIG_FLOOD_INGRESS_RATE}}$ m$^3$/s. A chamber is *flooded* once
$w_i \geq \Omega_i$; `flooded_fraction` reports the share of chambers flooded
at a time $t$. `critical_ingress` picks the single entry that floods the most
of the network by the horizon. The default "Main Strike" network has
${{FLOOD_CHAMBERS}}$ chambers and ${{FLOOD_TUNNELS}}$ tunnels totalling
${{FLOOD_TOTAL_VOLUME}}$ m$^3$ (see [@fig:flood_curve]).

## Race-form analytics and cover model

Raw race records are normalized to a seconds-per-furlong pace corrected for
going (firm/soft) and weight carried:
$\tau = (t - g\, d - \max(w - {{CORE_BASE_WEIGHT}},0)\,\epsilon\, d)/d$, with
$\epsilon = {{CORE_WEIGHT_SEC_PER_LB}}$ s per furlong per pound over the base
weight. The speed index is the seconds saved per furlong versus par,
${{CORE_PAR_SECONDS}} - \tau$. A horse's form rating is
the exponentially-weighted moving average of its speed indices, where a race
`age` before the newest is weighted $0.5^{\text{age}/\text{halflife}}$
(halflife ${{CONFIG_RACE_HALFLIFE}}$). Win probabilities follow a softmax
over ratings.

**Cover risk.** The stewards flag a horse whose performance improves by more
than $\theta = {{CORE_DETECTION_THRESHOLD}}$ speed-index units above its own
baseline. With
$n$ races and natural race-to-race variability $\sigma$, the standard error of
the mean performance is $\sigma/\sqrt{n}$, so applying a boost $b$ gives a
detection risk

$$ \mathrm{risk}(b) = \Phi\!\left(\frac{b - \theta}{\sigma/\sqrt{n}}\right), $$

the probability a normal draw with mean $b$ clears the threshold — the
detection-theoretic reading of stewards' scrutiny [@greenswets1966].
`cover_viability` returns `win_delta`, `detection_risk`, and
`expected_value = win_delta * PURSE - risk * DETECTION_PENALTY`, with
PURSE = {{CORE_PURSE}} and DETECTION_PENALTY = {{CORE_DETECTION_PENALTY}}
(both fixed in `race_analytics.py`). For the
${{CONFIG_COVER_BOOST}}$ boost to Pegasus (with
$\sigma = {{CONFIG_COVER_SIGMA}}$) the risk is ${{COVER_DETECTION_RISK}}$ and
expected value ${{COVER_EXPECTED_VALUE}}$ — a sustainable cover — whereas a
blatant boost is caught (see [@fig:race_cover]).

## Monopoly acquisition optimizer

The monopoly is a *selection* problem too: with a budget of
$K$ acquisitions ([@fig:acquisition_curve]), which independent fabricators
should ZORIN buy? The acquireable set is the ${{ACQ_ACQUIREABLE}}$ fabricators
(owners other than ZORIN). Each budget-$K$ subset is scored by the objective
`post_elimination_hhi(chain, acquired)` (or by ZORIN's fabrication share),
and `optimal_acquisition` exhaustively searches over every $K$-subset with
deterministic tie-breaking. `greedy_acquisition` is the hill-climbing baseline
that adds the single firm giving the largest score gain at each step. Because
the exhaustive search is optimal, $\mathrm{greedy} \le \mathrm{optimal}$
always; with the default budget of {{ACQ_BUDGET}} the optimal acquisition
(`{{ACQ_OPTIMAL_ACQUIRED}}`) lifts HHI from {{ACQ_BASELINE_HHI}} to
{{ACQ_OPTIMAL_HHI}}, a gain of {{ACQ_HHI_GAIN}} over buying nothing, while the
greedy baseline reaches {{ACQ_GREEDY_HHI}} (regret {{ACQ_REGRET}}). The same
optimality argument bounds the *scenario* acquisition
(`{{ACQ_SCENARIO_ACQUIRED}}`) from above, which is how Section [@sec:results]
scores the scheme's shortfall; the optimizer is a bound on the scenario, not a
description of it.

## Valley impact — the flood's urban blast-reach

ZORIN's sabotage is not the flood but its *consequence*. Each surface
fabrication plant (a `SurfaceFab`) is hydraulically coupled to a mine chamber;
water in that chamber raises the local water table by the fab's `leakage`
coefficient, and the fab becomes inoperable when that table reaches its
`foundation_elevation` — the coarse form of the groundwater-inundation damage
relation [@kreibich2008]:

$$ \mathrm{table}_{f}(t) = \ell_f \cdot h_{c(f)}(t), \qquad \text{inoperable if }
   \mathrm{table}_{f}(t) \ge z_f. $$

`valley_capacity_loss` reports the fraction of total fabricating capacity
inoperable by a decision time — for the default scenario {{VALLEY_INOPERABLE}}
of {{VALLEY_FABS}} fabs ({{VALLEY_LOSS}} of capacity) by the horizon
(see [@fig:valley_impact]). The {{VALLEY_SURVIVOR_COUNT}} survivors are
`{{VALLEY_SURVIVORS}}`: `zorin_fab` endures because it sits over the
low-coupling, high-separation `shaft_a`, which is the outcome the scheme
intends. The survivor and victim sets are determined purely by coupling
geometry, not by ownership, and the two directions come out differently: no
plant outside ZORIN's control survives
({{VALLEY_UNACQUIRED_SURVIVOR_COUNT}} such survivors), but
`{{VALLEY_ACQUIRED_VICTIMS}}` — a plant he acquires — is destroyed anyway.

## Racing betting market and cover finance

The cover is financed by betting on the controlled horse. `cover_bankroll`
takes the EWMA **form ratings** (a boost is in speed-index units, so it can
only be applied to a rating) and derives both sides of the trade from the same
softmax. The honest book is priced off the *un-boosted* win probabilities
$p_i = \mathrm{softmax}(r)_i$: `market_odds` converts them into decimal odds
under a bookmaker overround $\nu = {{CONFIG_MARKET_OVERROUND}}$ — the standard
way an outcome model is priced against a book [@dixon] — so the market's
implied probabilities sum to $\nu$: $q_i = p_i \nu$,
$\mathrm{odds}_i = 1/q_i$. Against that *honest* book, `cover_bankroll` prices
the manipulated horse using its boosted true probability
$p^\ast = \mathrm{softmax}(r + b e_{\text{Pegasus}})_{\text{Pegasus}}$, so the
edge measures the boost rather than a change of probability model: the value
edge is $p^\ast \mathrm{odds} - 1$, the
Kelly-optimal stake fraction is
$(p^\ast \mathrm{odds} - 1)/(\mathrm{odds} - 1)$ when positive, and the
expected profit is the edge times the staked bankroll. For Pegasus under a
${{CONFIG_COVER_BOOST}}$ boost the true probability
({{MARKET_TRUE_PROB}}) exceeds the market-implied ({{MARKET_IMPLIED}}),
giving a positive edge ({{MARKET_EDGE}}) and a Kelly stake of
{{MARKET_STAKE}} — precisely the anomaly that the cover-risk model of
`race_analytics` would eventually flag [@kelly1956].
