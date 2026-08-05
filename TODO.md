# TODO — a_view_to_a_kill (ZORIN)

`a_view_to_a_kill` is the PROJECT BOND film package for *A View to a Kill*
(1985): six pure, deterministic domain models of Max ZORIN's scheme (chip
supply chain, budgeted acquisition, mine flood, valley impact, race analytics,
race market), a metric layer driven entirely by `manuscript/config.yaml`, and
the FROZEN `bond_api.MissionProvider` adapter. Measured on this tree today
(`uv run pytest tests/ --cov=src --cov-fail-under=90`): **300 tests passing,
0 failed, 0 skipped, 99.17% line + branch coverage on `src/`** (6 uncovered
statements, all enumerated below). `ruff check`, `ruff format --check`, and
`mypy src/ scripts/` are all clean; `scripts/z_generate_manuscript_variables.py`
resolves 87 tokens strictly and re-renders 5 figures. All eight adversarial
audit findings in `output/verify/a_view_to_a_kill.json` were re-checked against
the tree this session: seven are fixed and gated, one is deliberately carried
as a stated limitation (see [Known limitations](#known-limitations)).

Completed phases live in the git log, not here. Live counts:
[`docs/_generated/COUNTS.md`](docs/_generated/COUNTS.md).

## Open work

11 items: 4 Correctness, 3 Verification, 1 Documentation, 3 Extension.

### Correctness

#### C1 — Six unreachable defensive statements are neither deleted nor marked

*Carried over from the unresolved audit findings
(`output/verify/a_view_to_a_kill.unresolved.json`, entry 3).*

Every reachable branch in `src/` is covered. Six statements remain uncovered,
and each is **unreachable through the public API** rather than untested.
Leaving them bare inflates the "missing" column, so a future real gap hides in
the noise.

| File:line | Statement | Why it cannot be reached |
|---|---|---|
| `src/a_view_to_a_kill/chip_supply_chain.py:188` | `raise ValueError(f"unknown supplier {name!r}")` in `_stage_of` | Private helper; `validate_graph` rejects links to unknown names first |
| `src/a_view_to_a_kill/chip_supply_chain.py:220` | `return {}` (`total <= 0`) in `market_share` | `Supplier.__post_init__` rejects non-positive capacity; `SupplyChain` rejects an empty supplier tuple |
| `src/a_view_to_a_kill/chip_supply_chain.py:375` | `return 0.0` (`total <= 0`) in `post_elimination_hhi` | Same two constructors |
| `src/a_view_to_a_kill/mine_flood.py:355` | `return 0.0` (`full.size == 0`) in `flooded_fraction` | `MineNetwork` rejects an empty chamber tuple |
| `src/a_view_to_a_kill/mine_flood.py:369` | `return 0.0` (`total_in <= 0`) in `water_balance_error` | `FloodParams` requires positive `ingress_rate` and `horizon` |
| `src/a_view_to_a_kill/valley_impact.py:174` | `return 0.0` (`total <= 0`) in `valley_capacity_loss` | `SurfaceFab` requires positive capacity; the empty-list case is handled and tested one branch earlier |

**Done when:** each of the six is either deleted (with the invariant that makes
it dead stated in the docstring) or carries `# pragma: no cover` plus a
one-line rationale, and the coverage report shows `Miss 0` for all three files.

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90 -q   # expect: no "Missing" column entries
```

#### C2 — Dead conditional in `market_odds` that coverage cannot see

`src/a_view_to_a_kill/race_market.py:95` reads
`implied = prob * overround / total if total else 0.0`. Lines 89–90 already
`raise ValueError` when `total <= 0`, so `total` is strictly positive by the
time line 95 runs and the `else 0.0` arm is unreachable. It is *not* in the C1
list because `coverage.py` does not branch-measure conditional expressions —
`race_market.py` reports 100% line + branch coverage with this dead arm in it.
That is a green-by-construction blind spot, not a covered branch.

**Done when:** line 95 is `implied = prob * overround / total` (no conditional),
and the suite still passes.

```bash
uv run pytest tests/test_race_market.py tests/test_validation_paths.py -v
```

#### C3 — `market_odds` silently renormalizes un-normalized input

`src/a_view_to_a_kill/race_market.py:75-97`. The docstring (lines 78–80) states
`q_i = p_i * overround` "(summing to `overround`)", but line 95 computes
`p_i * overround / Σp`. Those agree only when the input already sums to 1.
Demonstrated divergence:

```python
mkt.market_odds({"a": 80.0, "b": 20.0})   # ratings, not probabilities
# -> {'a': 1.116, 'b': 4.464}, implied sum 1.12 — accepted silently
```

This renormalization is precisely what made audit finding 3 (the cover-finance
bug: EWMA form ratings passed where probabilities were documented) produce
plausible-looking numbers instead of an exception. The model bug was fixed in
`0867663`; the laundering path that hid it is still open.

**Done when:** `market_odds` either (a) rejects input whose values do not sum to
1 within a stated tolerance, or (b) documents the normalization explicitly as
part of its contract — and a test pins whichever choice is made, including the
`{"a": 80.0, "b": 20.0}` case above.

```bash
uv run pytest tests/test_race_market.py -v
```

#### C4 — `market_odds` can emit decimal odds below 1.0

`src/a_view_to_a_kill/race_market.py:95-96`. When a normalized probability
exceeds `1 / overround`, the implied probability exceeds 1 and the decimal odds
drop below 1.0 — incoherent as a price (a winning bet returns less than the
stake). No guard exists. Demonstrated:

```python
mkt.market_odds({"a": 1.0, "b": 0.0}, 1.12)   # -> {'a': 0.8928..., 'b': inf}
```

`tests/test_race_market.py:23-29` asserts `all(o > 1.0)`, but only on the
shipped softmax book (max win probability ≈ 0.248, so `p·ν ≈ 0.278`). The
defect is **not reachable from the shipped scenario** — it is reachable through
the public API, which the pure core exposes as a reusable model.

**Done when:** `market_odds` raises when any `p_i * overround > 1`, with a test
that pins the raise on the `{"a": 1.0, "b": 0.0}` input above.

```bash
uv run pytest tests/test_race_market.py tests/test_validation_paths.py -v
```

### Verification

#### V1 — "`zorin_fab` endures" is hand-written prose with no gate behind it

`manuscript/02_methodology.md:161-162` ("`zorin_fab` endures because it sits
over the low-coupling, high-separation `shaft_a`, which is the outcome the
scheme intends") and `manuscript/03_results.md:122` ("`zorin_fab` is among them,
sitting over the low-coupling `shaft_a`") assert *which* fab survives as a
literal. Survivorship is scenario-dependent, and no test binds the claim.

`tests/test_manuscript_variables.py:216`
(`test_scenario_acquisition_names_are_never_hand_written_in_prose`) only guards
firms in the *acquisition* set, and `zorin_fab` is never acquired.
`tests/test_manuscript_variables.py:180`
(`test_valley_ownership_split_matches_the_manuscript_claim`) guards the
ownership split, not the identity of the survivor. Counterexample verified this
session — set `experiment.flood_ingress_rate: 200.0` and
`experiment.flood_horizon: 300.0` in `manuscript/config.yaml`:

```
victims   = {amd_fab, intel_fab, silicon_valley_fab, zorin_fab}
survivors = {nec_fab}
```

Every existing gate stays green (victims and survivors both non-empty, sets
disjoint, partition complete, `acquired_victims` non-empty,
`unacquired_survivors == []`), `{{VALLEY_SURVIVORS}}` updates correctly — and
both prose sentences are now false. This is the same defect class as audit
finding 2, on the flood side instead of the ownership side.

**Done when:** either the survivor identity reaches the page as a token, or a
test in `tests/test_manuscript_variables.py` asserts `zorin_fab` is in
`valley_metrics(scenario_from_config(...))["survivors"]` and fails on the
config above.

```bash
uv run pytest tests/test_manuscript_variables.py -v
```

#### V2 — The zero-probability odds branch is never exercised

`src/a_view_to_a_kill/race_market.py:96`:
`odds[name] = 1.0 / implied if implied > 0 else float("inf")`. The
`float("inf")` arm is reachable (`market_odds({"a": 1.0, "b": 0.0})` returns
`inf` for `b`) but no test in `tests/test_race_market.py` or
`tests/test_validation_paths.py` passes a zero probability. `race_market.py`
still reports 100% line + branch coverage, because `coverage.py` does not
branch-measure conditional expressions — the same blind spot as C2.

**Done when:** a test asserts `market_odds({"a": 1.0, "b": 0.0})["b"] ==
float("inf")` and pins the downstream behaviour of `implied_probability`,
`value_edge`, and `kelly_fraction` on an infinite odd (or C4's guard removes
the path entirely and the test asserts the raise).

```bash
uv run pytest tests/test_race_market.py -v
```

#### V3 — Greedy-vs-exhaustive regret is 0.0, so the comparison is non-discriminating

*Carried over from the unresolved audit findings
(`output/verify/a_view_to_a_kill.unresolved.json`, entry 3).*

Measured this session on the shipped graph: `ACQ_OPTIMAL_HHI = 1741.4`,
`ACQ_GREEDY_HHI = 1741.4`, `ACQ_REGRET = 0.0`. `tests/test_acquisition.py:71`
(`test_greedy_never_beats_optimal`) asserts
`greedy == pytest.approx(optimal) or greedy < optimal` — on this dataset the
equality arm always fires, so the test would still pass if `greedy_acquisition`
were rewritten to call `optimal_acquisition`. The exhaustive optimizer is
supposed to be the correctness oracle for the greedy baseline; on this data it
is not proving anything about greedy.

**Done when:** a second documented market fixture exists on which greedy
demonstrably loses (`regret > 0`), and a test asserts a strictly positive regret
on it, so the oracle has a discriminating case.

```bash
uv run pytest tests/test_acquisition.py -v
```

### Documentation

#### D1 — No standing check that sibling packages track corrected ZORIN numbers

Commit `0867663` corrected the cover-finance model, moving the published
figures (implied 0.245→0.238, edge 0.0127→0.0415, Kelly stake 414→1298,
expected profit 5→54). Verified this session: no artifact under this package
carries the pre-correction values, and the suite-level
`../bond-manuscript/manuscript/03_14_a_view_to_a_kill.md` already carries the
corrected ones (0.238 / 0.0415 / 1298). Nothing is stale today — but nothing
prevents it going stale either, because that sibling manuscript is a hand-copied
prose snapshot of this package's abstract, not a generated artifact.

**Done when:** either the sibling section is generated from this package's
resolved `output/manuscript/00_abstract.md`, or a check in the suite tooling
compares the two and fails on divergence.

```bash
grep -c "0.238" ../bond-manuscript/manuscript/03_14_a_view_to_a_kill.md   # expect: 1
```

### Extension

#### E1 — `fab_inoperable_at` is a linear scan over the flood series

`src/a_view_to_a_kill/valley_impact.py:144`. It walks the flood result step by
step, `O(steps)` per fab. Fine at the current horizon (900 s at `dt = 1.0`).
The water-table series is monotone, so a bisection is available.

**Done when:** the horizon grows enough for it to matter *and* a bisection
replaces the scan while `tests/test_valley_impact.py` stays green with
identical outputs. Not worth doing before then.

```bash
uv run pytest tests/test_valley_impact.py -v
```

#### E2 — `optimal_acquisition` is exhaustive `C(n, K)`

`src/a_view_to_a_kill/acquisition.py:99`. Deliberately exhaustive: it is the
correctness oracle for `greedy_acquisition` (line 129). With 3 acquireable
firms this is trivial.

**Done when:** the acquireable set exceeds roughly a dozen firms — then add a
branch-and-bound path for production use and keep the exhaustive path as the
test oracle. Do not replace the exhaustive path.

```bash
uv run pytest tests/test_acquisition.py -v
```

#### E3 — Provenance is recorded inline instead of via `bond-utilities`

`src/a_view_to_a_kill/mission.py:215` constructs `Provenance(...)` directly.
The Q-BRANCH package `bond-utilities` is not yet an installable dependency of
this tree.

**Done when:** `bond-utilities` ships as an installable dependency, and
`mission.py` delegates provenance persistence to
`bond_utilities.mission_io.record_provenance_outcome` with
`tests/test_mission.py` still asserting `seed == 1985` and a stable
`input_hash`. No rework of the pure core is required.

```bash
uv run pytest tests/test_mission.py -v
```

## Known limitations

Deliberately out of scope or accepted. These are **not** TODO items; they are
recorded so nobody re-litigates them.

- **ZORIN's acquisition is suboptimal, and the package says so rather than
  quietly switching sets.** The film-faithful scenario buys
  `amd_fab, nec_fab` (HHI 1528.9, fab share 0.680); the optimizer's answer on
  the same budget is `intel_fab, nec_fab` (HHI 1741.4, share 0.820) — a
  shortfall of 212.5 HHI points. This was audit finding 5 and is carried in
  `output/verify/a_view_to_a_kill.unresolved.json` (entry 2) as reported, not
  closed. `manuscript/03_results.md` §"Scenario versus optimizer" and
  `manuscript/00_abstract.md` both state it. **Honest scope:** every
  scenario-conditioned number in the manuscript (HHI, fab share, cascade,
  valley split) is conditioned on `experiment.scenario_acquired_firms` in
  `manuscript/config.yaml`, *not* on the optimizer's answer. The package makes
  no claim that ZORIN's scheme is optimal. Do not "fix" this by pointing the
  scenario at the optimizer's set — that would delete the finding, not resolve
  it.

- **The cover-finance correction is disclosed, not reversible.** Correcting
  `cover_bankroll` (commit `0867663`) changed the published figures; the
  manuscript now carries the corrected values as tokens
  (`output/verify/a_view_to_a_kill.unresolved.json`, entry 1). Any artifact
  exported *before* that commit quotes numbers this package no longer produces.
  In-tree staleness was checked this session and is clean; the standing risk is
  tracked as D1.

- **Coverage floor stays at 90%.** The BOND preamble fixes it there. Measured
  coverage is 99.17%, but raising the local floor would diverge from the fleet
  gate.

- **`acquisition.py` has no price or valuation model.** The budget is a *count*
  of acquisitions by design. A monetary model is a different paper.

- **The datasets are model parameters, not measured field data.** The supply
  graph, mine geometry, valley fabs, and race card are documented, fixed,
  deterministic reconstructions — stated in `data/claim_ledger.yaml` and
  `manuscript/05_experimental_setup.md`. Their job is to make the mathematics
  reproducible and testable, not to describe the 1985 semiconductor market.

- **The resolved manuscript *is* byte-identical across reruns** (fixed
  2026-08-05; this entry previously recorded the opposite). `GENERATION_TIMESTAMP`
  was a `datetime.now(timezone.utc)` reading rendered into
  `output/manuscript/05_experimental_setup.md` and
  `output/data/manuscript_variables.json`, so those two files changed on every
  regeneration while `AGENTS.md`, `manuscript/02_methodology.md`, and
  `manuscript/06_reproducibility.md` all claimed byte-identical reruns. Scoping
  the guardrail around the token, as this entry used to, was a narrowed claim
  rather than a fix. The token is now `MANUSCRIPT_DATE`, read from `paper.date`
  in `manuscript/config.yaml`; the `now=` injection point is gone; and
  `tests/test_regeneration_determinism.py` runs the real generator twice in two
  processes, with real elapsed time between them, and diffs every persisted
  byte. The old `now=`-injection determinism test was the reason the breach
  survived — it pinned the varying input, so it could not fail.

- **`bond-utilities` is not a dependency, and `bond-orchestrator` needs no
  wiring.** `mission.py` is the only `bond_api` importer and the package
  resolves it lazily (PEP 562), so the pure core, figures, and manuscript
  pipeline all run when `bond-api` is absent —
  `tests/test_bond_api_fallback.py` pins this with a real import blocker plus
  positive and negative controls. The orchestrator discovers this film by slug
  `a_view_to_a_kill` via `bond_api.discovery`; `MissionProvider` is at module
  top level. Nothing further is required. (Adoption of the shared provenance
  helper is E3.)

## Verification

All of these must pass before a commit. Run from
`/Users/4d/Documents/GitHub/template/projects/working/bond/a_view_to_a_kill`.

| Command | Expected outcome (measured this session) |
|---|---|
| `uv run pytest tests/ --cov=src --cov-fail-under=90` | 300 passed, 0 failed, 0 skipped; 99.17% total; only `chip_supply_chain.py:188,220,375`, `mine_flood.py:355,369`, `valley_impact.py:174` in the Missing column |
| `uv run ruff check src/ scripts/ tests/` | `All checks passed!` |
| `uv run ruff format --check src/ scripts/ tests/` | `35 files already formatted` |
| `uv run mypy src/ scripts/` | `Success: no issues found in 18 source files` |
| `uv run python scripts/z_generate_manuscript_variables.py` | 87 tokens resolved strictly, 9 manuscript sections written, 5 figures rendered; zero `{{` left in `output/manuscript/` |
| `git status --short` | empty after a path-scoped commit (`output/` is gitignored) |

Targeted suites:

```bash
uv run pytest tests/test_mission.py -v              # the FROZEN MissionProvider surface
uv run pytest tests/test_bond_api_fallback.py -v    # the no-bond_api fallback, with a real import blocker
uv run pytest tests/test_metrics_scenario.py -v     # every config knob must move a computed metric
uv run pytest tests/test_claim_ledger.py -v         # the ledger names generators and tokens, never numerals
uv run pytest tests/ --collect-only -q | tail -1    # test count alone
```

If `uv` fails with `Failed to initialize cache at /Users/4d/.cache/uv`, the
call is sandboxed — re-run it with the sandbox disabled. If `pyproject.toml`
changes, sync with `uv sync --all-extras`; a bare `uv sync` prunes pytest and
`uv run pytest` then silently resolves a different interpreter.
