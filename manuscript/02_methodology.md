# Methodology {#sec:methods}

All three models are pure functions of fixed, documented datasets; no random
draws, no external state, no wall-clock dependence. This guarantees
byte-identical reruns.

## Microchip supply-chain monopoly analysis

The supply chain is a directed graph of firms $V$ (nodes) and supply links
$E \subseteq V \times V$ (edges flowing forward through stages
`wafer -> fabrication -> assembly -> distribution`). Each firm $v$ has a
throughput capacity $c_v$. The default dataset is a documented
reconstruction of the mid-1980s semiconductor market (${{SC_NODES}}$ firms,
${{SC_LINKS}}$ links).

**Concentration.** Within a stage (or the whole graph), firm $v$'s capacity
share is $s_v = c_v / \sum_u c_u$, and the Herfindahl-Hirschman index is
$\mathrm{HHI} = 10000 \sum_v s_v^2$, ranging from $0$ (perfect competition)
to $10000$ (monopoly). The default market opens at
HHI ${{SC_HHI_BEFORE}}$.

**Choke points.** Structural choke points are measured with Brandes'
betweenness-centrality algorithm: a firm's betweenness is the fraction of
ordered node pairs for which it lies on a shortest directed supply path.
Wafer sources carry zero betweenness by construction; the top choke point is
`{{SC_TOP_CHOKE}}` (see [@fig:choke_points]).

**Single-source dependence.** A downstream firm whose only upstream supplier
is one firm is a single point of failure; such dependencies are the monopolist's
pressure points.

**Cascade failure.** Removing a set $R$ of firms (acquired-and-dismantled
competitors), a downstream firm is *starved* if it has no directed supply path
from any surviving wafer supplier. The starved fraction is
$\sum_{v \in S} 1 / |V|$.

**The ZORIN attack.** ZORIN owns `zorin_fab` and `zorin_assembly`; by
acquiring the independent fabricators `amd_fab` and `nec_fab` and eliminating
the rest of the market, his fabrication share rises to
${{SC_ZORIN_FAB_SHARE}}$ and market-wide HHI jumps to ${{SC_HHI_AFTER}}$.
Formally, `monopoly_share` computes ZORIN's surviving capacity share per
stage once every non-acquired independent is removed, and
`post_elimination_hhi` merges ZORIN's holdings into one entity before
recomputing concentration.

## Flood-the-mine water-ingress dynamics

The mine is a network of chambers (nodes) and bidirectional tunnels (edges).
Chamber $i$ has volume $\Omega_i$, horizontal cross-sectional area $A_i$, and
elevation $z_i$; water level is $h_i = z_i + w_i / A_i$ where $w_i$ is the
water volume in the chamber. Tunnels have cross-sectional area $a_{ij}$.

Water enters at designated ingress chambers at total rate $Q$ (split evenly),
and flows through each tunnel from the higher-head end to the lower under a
simplified weir law

$$ q_{ij} = C\, a_{ij}\, \sqrt{\max(h_i - h_j,\, 0)}, $$

with discharge coefficient $C = 0.6$. Each timestep's tentative flows are
scaled so no chamber lends more water than it holds, making the scheme
**exactly mass-conserving**. State evolves by explicit Euler with timestep
$1$ s to horizon ${{CONFIG_FLOOD_HORIZON}}$ s at ingress
${{CONFIG_FLOOD_INGRESS_RATE}}$ m$^3$/s. A chamber is *flooded* once
$w_i \geq \Omega_i$; `flooded_fraction` reports the share of chambers flooded
at a time $t$. `critical_ingress` picks the single entry that floods the most
of the network by the horizon. The default "Main Strike" network has
${{FLOOD_CHAMBERS}}$ chambers and ${{FLOOD_TUNNELS}}$ tunnels totalling
${{FLOOD_TOTAL_VOLUME}}$ m$^3$ (see [@fig:flood_curve]).

## Race-form analytics and cover model

Raw race records are normalized to a seconds-per-furlong pace corrected for
going (firm/soft) and weight carried:
$\tau = (t - g\, d - \max(w - 126,0)\,\epsilon\, d)/d$. The speed index is the
seconds saved per furlong versus par, $14.0 - \tau$. A horse's form rating is
the exponentially-weighted moving average of its speed indices, where a race
`age` before the newest is weighted $0.5^{\text{age}/\text{halflife}}$
(halflife ${{CONFIG_RACE_HALFLIFE}}$). Win probabilities follow a softmax
over ratings.

**Cover risk.** The stewards flag a horse whose performance improves by more
than $\theta = 1.0$ speed-index units above its own baseline. With
$n$ races and natural race-to-race variability $\sigma$, the standard error of
the mean performance is $\sigma/\sqrt{n}$, so applying a boost $b$ gives a
detection risk

$$ \mathrm{risk}(b) = \Phi\!\left(\frac{b - \theta}{\sigma/\sqrt{n}}\right), $$

the probability a normal draw with mean $b$ clears the threshold. `cover_viability`
returns `win_delta`, `detection_risk`, and
`expected_value = win_delta * PURSE - risk * DETECTION_PENALTY`. For the
${{CONFIG_COVER_BOOST}}$ boost to Pegasus (with
$\sigma = {{CONFIG_COVER_SIGMA}}$) the risk is ${{COVER_DETECTION_RISK}}$ and
expected value ${{COVER_EXPECTED_VALUE}}$ — a sustainable cover — whereas a
blatant boost is caught (see [@fig:race_cover]).
