# Booster model specification (S4, for `prereg-v2`)

This document fixes the probabilistic model of one English booster pack for
the three selected sets (Stellar Crown (sv07), Surging Sparks (sv08) and
Destined Rivals (sv10) before any price value is used in an analysis. It
refines protocol §4 (`prereg-v1`); departures from `prereg-v1` are recorded in
[ADR 0010](../../docs/decisions/0010-booster-model-and-prereg-v1-deviations.md).

Every rule below is classified:

- **Documented**: stated by the source that produced the pull-rate data
  (TCGplayer Authentication Center articles) and by at least one independent
  source.
- **Assumed**: not documented; the central value is a named, parameterised
  assumption, and the alternative enters as a robustness scenario.

## 1. Sources read for the pack structure (accessed 2026-11-15)

| Source | What was read | Used for |
|---|---|---|
| TCGplayer, *Pokémon TCG: Stellar Crown Pull Rates* (P. Day) | Full article: per-rarity rates with 95 % half-widths (normal approximation), slot of each rarity, note on Dachsbun ex | Slots, rates per dataset, short print |
| TCGplayer, *Pokémon TCG: Surging Sparks Pull Rates* (P. Day) | Full article: same content; "more than 8,000 booster packs" | Slots, rates per dataset |
| TCGplayer, *Pokémon TCG: Destined Rivals Pull Rates* (P. Day) | Full article: same content (no ACE SPEC rarity in this set) | Slots, rates per dataset |
| Bulbapedia, *Booster pack (TCG)* | "International releases" table for Scarlet & Violet packs | Slot layout, ACE SPEC period (Temporal Forces to Prismatic Evolutions) |
| PokéBeach, *"Scarlet & Violet" Booster Pack Configuration Finally Revealed* (7 Mar 2023) | Full article: 4 C, 3 U, 2 reverse holos, 1 holo, Basic Energy, code card; IR and SIR replace the second reverse | Slot layout; places Hyper Rare in the holo slot (conflict, §3) |

URLs are in `research/reports/tcgplayer_published_rates.csv` (TCGplayer) and in
the bibliography. The per-rarity figures transcribed from the TCGplayer
articles are in that CSV.

## 2. Pack contents (central layout `tcgplayer`)

| Slot | Content | Outcomes and probabilities | Status |
|---|---|---|---|
| `c1`–`c4` | 4 Common | a Common card, base printing | Documented |
| `u1`–`u3` | 3 Uncommon | an Uncommon card, base printing | Documented |
| `rev1` | first reverse holo | ACE SPEC Rare with p_ACE (sv07, sv08); otherwise a reverse-holo printing | Documented (TCGplayer: ACE SPEC "in the first Reverse Holo slot") |
| `rev2` | second reverse holo | Illustration Rare, Special Illustration Rare or Hyper Rare with p_IR, p_SIR, p_HR; otherwise a reverse-holo printing | Documented (TCGplayer, Bulbapedia) |
| `rare` | rare slot | Double Rare or Ultra Rare with p_DR, p_UR; otherwise a Rare | Documented (TCGplayer: DR and UR "in the Rare slot") |
| n/a | Basic Energy, code card | not valued (value 0) | Documented content; value 0 assumed |

Pools of printings (`pokequant_core.booster.build_pools`):

- *Base printing* of a card: `normal` for Common and Uncommon, `holo` for Rare
  and above (all SV-era Rares are holofoil); if that printing does not exist,
  the other one.
- *Reverse pool*: every `reverse` printing of the set (Common, Uncommon and
  Rare cards: 125, 165 and 165 printings in sv07, sv08, sv10).
- *Hit pools*: the base printing of each card of the rarity.

The outcomes of one slot are mutually exclusive by construction (one card per
slot), so each random slot has a Dirichlet posterior (§4).

## 3. Assumptions and their scenarios

| ID | Assumption (central) | Evidence | Alternative scenario |
|---|---|---|---|
| A-HR | Hyper Rare is in `rev2` | TCGplayer (3 articles), Bulbapedia | **R12**: Hyper Rare in `rare` (PokéBeach, pre-release 2023) |
| A-EQ | Within a pool, printings are equally likely | TCGplayer: per-card rates fit the rarity interval, "which supports the assumption" | **R11**: Dachsbun ex Double Rare (sv07-067) at the observed relative rate 0.76 / 1.21 of the other Double Rares (TCGplayer note) |
| A-IND | Slots are independent of each other | No source reports co-occurrence; layout allows a hit in `rev1`, `rev2` and `rare` together | Not testable with the data; stated as a limit |
| A-REV | `rev1` and `rev2` draw from the same reverse pool | Not documented | Stated as a limit (small value effect) |
| A-CU | Commons and Uncommons of one pack are distinct cards (draws without replacement within the 4 C and the 3 U) | Collation practice, not documented | Draws with replacement (numerical check in S5) |
| A-GOD | No "god pack" or special collation in English packs of these sets | None found in the sources above | n/a |
| A-STAB | Rates measured at release hold for the product analysed | Openings date from release week (2024-09-13 to 2025-05-30) | Stated as a limit |

## 4. Estimation of the slot probabilities

Registry rows give, per set and rarity, `hits` and `packs` that the registry
reconstructed from published rates and 95 % half-widths. Checks run in S4:

- The registry interval of every row of the three sets is exactly the Jeffreys
  equal-tailed interval of its `hits`/`packs` (|Δ| < 10⁻⁵; test
  `test_registry_intervals_are_jeffreys_on_the_published_counts`). 232 of the
  234 registry rows match to 10⁻⁴; the two exceptions are in 30th Celebration,
  outside the sample.
- The TCGplayer sample size implied by each published rate and half-width,
  n = p(1 − p)(1.96 / h)², reproduces the registry count of the single-dataset
  row (sv10 Double Rare: 8,655 packs). The registry rows are therefore sums of
  per-dataset reconstructed counts.

Posterior for a random slot *s* with observed outcomes k = 1…K (rates from the
registry) and residual outcome 0 (reverse printing or Rare):

    (p₀, p₁, …, p_K) ~ Dirichlet(w·x₀ + a₀, w·x₁ + a₀, …, w·x_K + a₀)

- x_k = (hits_k / packs_k) · n_s, with n_s = min_k packs_k (rows of one set have
  different denominators; the smallest is the conservative common sample size),
  and x₀ = n_s − Σ x_k.
- a₀ = ½ (Jeffreys). Robustness **R8**: a₀ = 1 (uniform).
- w = 1 in the central analysis. Robustness **R9b** (replaces pre-registered
  test 9, ADR 0010): w = ½, i.e. half the effective sample size for every row,
  since all rows of the selected sets have reconstructed counts.
- Each slot is estimated independently; the `rev1` slot of sv10 is
  deterministic (no ACE SPEC rarity).

Epistemic draws (outer loop, S5) sample each slot's Dirichlet independently;
the posterior-mean model uses the Dirichlet means.

## 5. Pooling and heterogeneity (decision rule fixed before the test is run)

Each row pools the TCGplayer dataset with one second opening series (except
sv10 Double Rare: TCGplayer only). Per-dataset counts are not published; they
are approximated as follows: TCGplayer n and hits from its published rate and
half-width (§4), second dataset = pooled row − TCGplayer. These are
approximations of approximations, and the test is reported as such.

Rule: a Pearson χ² homogeneity test (2 datasets, 1 d.f.) is run for every row
with two datasets (16 rows). With Holm–Bonferroni at family-wise level 0.05,

- if no row rejects homogeneity, pooling stands and is reported;
- if any row rejects it, the central analysis keeps the pooled registry rows
  and robustness **R13** re-runs the analysis with TCGplayer-only rates for
  the affected set.

Script: `scripts/check_homogeneity.py`; output: `research/reports/homogeneity.csv`.

**Result (run 2026-11-15, after the rule above was written):** 16 rows tested,
none rejected (smallest p = 0.154, sv08 Special Illustration Rare; all
expected counts ≥ 12.7). Pooling stands; R13 is not triggered.

## 6. Closed-form quantities

Implemented in `pokequant_core.model` and tested (hypothesis property tests):

- P(card c in slot s) = P(R_s = pool(c)) / |pool(c)|.
- P(hit c) = 1 − ∏_s [1 − P(c in s)] (under A-IND).
- P(≥ 1 hit in n packs) = 1 − (1 − p)ⁿ; E[packs to first hit] = 1 / p;
  smallest n with P(≥ 1 hit) ≥ q.

## 7. What the model does not claim

- No exact distribution for undocumented rules: each enters as a scenario.
- Rates describe release-period product (A-STAB).
- Values of the Basic Energy and code card are set to 0.
