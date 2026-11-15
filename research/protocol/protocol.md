# Research protocol

> **Status: v1, candidate for pre-registration** (2026-11-15). Based on the
> internal *Protocole scientifique et plan du papier* (v1.0, 2 Nov 2026), the
> amendments of [ADR 0003](../../docs/decisions/0003-amendments-to-plan-v1.md)
> and the S1 work ([scoping note](scoping_note.md)).
> Frozen by the git tag `prereg-v1`. After that tag, any change is a documented
> deviation (ADR + reported in the paper).
> The analysis plan (sets, product, budgets, baskets, n_max, scenarios) is
> frozen at the end of S4 (tag `prereg-v2`) in `research/experiments/`.

**Objective:** an honest, reproducible and falsifiable study. The paper does not
try to show that boosters are profitable or not; it measures under which
conditions, and with what uncertainty, acquisition strategies differ.

## 1. Title and question

**Working title:** *Opening or Buying? A Probabilistic and Risk-Adjusted
Comparison of Pokémon TCG Booster Acquisition and Secondary-Market Purchases.*

**Main question:** to what extent is opening Pokémon TCG boosters an
economically competitive acquisition strategy compared with buying cards
directly on the secondary market, once pull-rate uncertainty, value dispersion,
fees and liquidity are taken into account?

### 1.1 Sub-questions

- **Q1**: What is the value distribution of the cards obtained by opening, not only its mean?
- **Q2**: Above which booster price does opening become economically comparable to buying a target card or basket directly?
- **Q3**: How much does pull-rate uncertainty change the conclusions?
- **Q4**: Do conclusions change with the set, booster price, price window and transaction costs?
- **Q5**: Do strategies have different risk profiles (probability of loss, quantiles, CVaR, capital tied up)?

### 1.2 Hypotheses (to pre-register)

| Code | Testable hypothesis | Indicator / test |
|---|---|---|
| H1 | The gross expected value of a booster is not sufficient to characterise the economic interest of opening. | Mean, median, P(loss), quantiles, CVaR. |
| H2 | Pull-rate estimation uncertainty can change the ranking of strategies. | Simulation under rate posteriors; sensitivity analysis. |
| H3 | Fees and liquidity reduce the apparent advantage of high listed-value cards. | Net realisable price; delay and cost scenarios. |
| H4 | The ranking opening vs direct purchase varies across sets and price regimes. | Multi-set comparison; time windows. |

These hypotheses are not anticipated conclusions. They can be rejected, and
negative or inconclusive results are reported.

### 1.3 Claimed contribution (cautious wording)

A reproducible framework combining (i) a probabilistic representation of booster
structure, (ii) Bayesian uncertainty on community-estimated pull rates,
propagated through a nested Monte Carlo, (iii) typed market prices converted
into net realisable values with explicit fees and liquidity scenarios, and
(iv) a risk-adjusted comparison with direct purchase under two pre-registered
estimands (E1, E2; §6.3).

The contribution is **not** to be the first odds calculator, EV calculator or
pack-opening simulator: practitioner tools already simulate outcome
distributions with fixed pull rates, and Mota (2026) formalises a
sealed-opened spread for Magic: The Gathering. The current novelty statement
is in [`literature_review.md`](literature_review.md) §4 and stays provisional
until the closest papers are read in full. It is not part of the
pre-registration.

### 1.4 What the paper does not claim

- Official pull probabilities when they are not published.
- Certain prediction of future card prices.
- A guaranteed financial return from opening.
- P(PSA 10) for a raw card from a population report.
- Generalisation to all sets, languages, countries and periods from a small sample.

## 2. Literature axes

| Axis | Concepts | Role in the paper |
|---|---|---|
| Collectibles & alternative assets | Passion assets, segmentation, demand, scarcity. | Justify the field and value drivers. |
| Hedonic pricing | Price explained by observable attributes. | Valuation baseline. |
| Probabilistic simulation | Monte Carlo, discrete distributions, parameter uncertainty. | Opening engine. |
| Risk measurement | Quantiles, downside risk, CVaR / expected shortfall. | Compare profit distributions. |
| Market liquidity | Spread, volume, time to sale, listed vs realised price. | Theoretical → realisable value. |
| Selection bias in grading | Self-selection, survivorship, population reports. | Frame the future grading module. |

The two leads of the v1.0 protocol were identified in S1: Danz (2026,
Princeton senior thesis, restricted access) and Baro (2026, SSRN). Neither
abstract models boosters or pull rates. Full review and references:
[`literature_review.md`](literature_review.md),
[`references.bib`](../paper/references.bib).

## 3. Empirical design

### 3.1 Population and sample

- 1–3 sets selected by a data-coverage audit, not personal preference. The
  selection rule is written in S2 **before** prices are inspected: (1) pull-rate
  sample size and share of non-reconstructed counts in the Poké Life registry,
  (2) documented slot structure, (3) share of cards with a usable price.
- English-language products only for the main analysis (largest pull-rate
  samples; one catalogue language).
- One exact sealed product (single booster, display, ETB) and its configuration; configurations are never mixed without an explicit model.
- Languages and variants fixed; an English and a Japanese card are different observations.
- A reference date for each price and a common time window.
- Commons/uncommons included only if their value is observable consistently; otherwise the low-value treatment is documented.

### 3.2 Variables

| Block | Minimal variables |
|---|---|
| Card | printing_id, set_id, card_number, rarity, variant, language, release_date |
| Pull rate | slot_id, rarity, hits, packs, rate, interval, confidence, dataset, date |
| Price | amount, currency, condition, grade, source, price_type, observed_at, sample_count if available |
| Product | booster_cost, pack_configuration, source, date |
| Costs | shipping, tax, marketplace_fee, payment_fee, grading_fee if applicable |
| Simulation | seed, N, model_version, data_snapshot, parameters |
| Liquidity | sales_count, listing_count, time_to_sale if legally available; otherwise an explicitly identified proxy |

## 4. Probabilistic model

### 4.1 Slot model

For slot *s*, rarity distribution P(R_s = r) and, conditional on rarity, card
distribution P(C = c | R_s = r, s, set):

    P(C = c in slot s) = P(R_s = rarity(c)) · P(C = c | R_s = rarity(c), s, set)

With conditionally independent slots:

    P(hit c) = 1 − ∏_s [1 − P(C = c in slot s)]

Valid only under slot independence. Replacement or exclusivity rules are
modelled explicitly; unknown rules are parameterised scenarios, not facts.

### 4.2 Estimation uncertainty

- **Binary rate** (x hits in n packs): p̂ = x/n with an appropriate interval;
  posterior p ~ Beta(x + ½, n − x + ½) (Jeffreys).
- **Slot with k mutually exclusive outcomes** (amendment A4): posterior
  (p₁,…,p_k) ~ Dirichlet(x₁ + ½, …, x_k + ½), which respects Σp = 1.
- Document the prior, the cases x = 0 and x = n, and any counts reconstructed
  from a rate and a margin (never treated as exact observations).
- If the registry aggregates heterogeneous sources or products, test
  heterogeneity across datasets before pooling.

### 4.3 Two kinds of uncertainty (amendment A5)

| Type | Question | Treatment |
|---|---|---|
| Aleatory | With known rates, how much do outcomes vary across openings? | Inner loop: M simulated packs at fixed parameters. |
| Epistemic | How badly are the rates themselves estimated? | Outer loop: K parameter draws from the posterior, or sensitivity scenarios. |

Every reported metric carries its Monte Carlo standard error.

### 4.4 Validation checks

- Toy case: one slot, two cards, known probability; exact mean and variance.
- Simulated frequencies vs theoretical probabilities.
- Hit counts vs binomial when assumptions allow.
- N = 10³, 10⁴, 10⁵, 10⁶: Monte Carlo error decays ∝ 1/√N.
- Dependent-slot and uncertain-rate scenarios.
- Fixed seed and saved parameters for every figure.

### 4.5 Packs until a hit

With independent per-pack probability p: N ~ Geometric(p), E[N] = 1/p, and
P(≥ 1 hit in n packs) = 1 − (1 − p)ⁿ. Presented as a simplified model, adapted
if the product has collation constraints.

## 5. Valuation and secondary market

### 5.1 Price hierarchy

| Type | Interpretation | Use |
|---|---|---|
| Active listing | Asking price; may be unrealistic. | Supply proxy, not a transaction value. |
| Provider market price | Platform aggregate with its own method. | Indicative benchmark; cite the provider. |
| Realised sale | Price actually paid, if available and allowed. | Most relevant measure of realised price. |
| Window median | Median of same card/condition/currency over a period. | Reduces outliers if N is sufficient. |
| Seller net price | Realised price minus fees and selling costs. | Realisable value used to compare strategies. |

### 5.2 Hedonic baseline (only if data allows)

    ln(P_it) = β₀ + β₁ R_i + β₂ A_it + β₃ G_i + β₄ D_it + β₅ L_it + δ_s + ε_it

R: rarity; A: age since release; G: grade/condition; D: demand proxy;
L: liquidity proxy; δ_s: set fixed effect. For the MVP, observed prices and
scenarios may be more honest than an under-powered regression.

### 5.3 Liquidity and costs

Net value includes seller fees, payment fees, shipping/insurance, applicable
taxes and grading costs if any. Unobserved time to sale is never invented:
use labelled scenarios (fast sale, slow sale, haircut).

### 5.4 Time and leakage

- Every observation is timestamped; an estimate at date t uses only information available at t.
- Train / validation / test splits are chronological, never random, for temporal data.
- Current prices are never used to reconstruct past values.
- If history is too short, no temporal prediction; scenario analysis only.

## 6. Strategies and estimands

### 6.1 Prices used

For a card printing c at reference date t₀:

- **Acquisition price** a(c): what a buyer pays: price + buyer fees + shipping.
- **Liquidation value** ℓ(c): what a seller receives: realisable price −
  seller fees − payment fees − shipping/insurance, after the liquidity scenario
  (haircut, or 0 for unsellable bulk in the prudent scenario).

Always ℓ(c) ≤ a(c). Gross scenarios (no fees, provider market price) are
reported only as a theoretical reference, never as the main result.

**Static design.** The main analysis uses a single reference date t₀ (one price
snapshot): no price dynamics, no holding-period return. Time enters only
through robustness on other snapshot dates (H4). This is a deliberate limit,
stated in the paper.

### 6.2 Strategies

- **A: Opening.** Buy n boosters at unit cost b (incl. taxes and shipping) and
  liquidate everything obtained.
- **B: Direct purchase.** Buy a target card or basket defined **ex ante** in the
  experiment configs (tag `prereg-v2`); no a-posteriori best basket.
- **C: Raw + grading** (extension, excluded from main results).
  EV = Σ_g P(G = g | X) · V_g − purchase − grading − shipping − selling fees.
  P(G | X) requires a representative sample of documented raw cards, never the
  PSA population report alone.

### 6.3 Estimands

The research question mixes two economically different uses of boosters. Both
are reported, separately:

- **E1: Budget liquidation.** With budget B, Strategy A opens n = ⌊B / b⌋
  boosters. Net profit of simulated opening j:
  Π_j = Σ_{cards i obtained} ℓ(C_ij) − n·b.
  Strategy B at the same date has a near-deterministic profit
  Π_B = Σ_{c ∈ basket} [ℓ(c) − a(c)] ≤ 0 (the round-trip cost), so E1 compares a
  risky distribution with a known transaction cost.
- **E2: Target acquisition cost.** Goal: own one copy of target card c\*.
  Strategy A opens boosters until the first c\* (capped at n_max, a
  pre-registered limit) and liquidates every other card. Net cost of run j:
  K_j = k_j·b − Σ_{other cards i} ℓ(C_ij), where k_j is the number of boosters
  opened (if the cap is reached without a hit, the run is a failure and c\* is
  then bought directly at a(c\*)). Strategy B costs a(c\*).
  Main quantity: P(K < a(c\*)) and the distribution of K − a(c\*).

## 7. Metrics and comparison protocol

### 7.0 Definitions and sign conventions

Π denotes a net profit (E1) or minus a net cost (E2, Π = a(c\*) − K, so that
Π > 0 means opening was cheaper). Losses are negative profits. Risk measures
are reported **as positive losses**:

- q_α(Π): α-quantile of Π.
- VaR_α = −q_α(Π).
- CVaR_α = −E[Π | Π ≤ q_α(Π)]; estimator: minus the mean of the ⌈αN⌉ smallest
  simulated values.
- α = 5 % for both. A tail estimate must rest on at least 1 000 tail samples
  (N ≥ 20 000 per epistemic draw for α = 5 %).

| Metric | Definition |
|---|---|
| Net EV | E[Π], mean simulated net profit. |
| Median | q₀.₅(Π). |
| P(loss) | P(Π < 0). |
| Quantiles | q₀.₀₅, q₀.₂₅, q₀.₇₅, q₀.₉₅ of Π. |
| VaR 5 % | −q₀.₀₅(Π). |
| CVaR 5 % | −E[Π \| Π ≤ q₀.₀₅(Π)]. |
| Break-even booster price | b\* = E[Σ_i ℓ(C_i)] for one booster (E1): net EV = 0 when b = b\*. |
| P(target hit in n) | 1 − ∏_{packs}(1 − p_hit) under independence; simulated otherwise. |
| Expected packs to hit | 1 / p_hit under independence. |
| Uncertainty interval | 2.5 %–97.5 % interval of each metric over epistemic draws. |
| Monte Carlo error | Standard error of each metric over the aleatory draws (batch means or bootstrap for quantiles and CVaR). |

### 7.0b Pre-registered decision rules for H1–H4

A strategy comparison is called **decisive** when the posterior probability
(share of epistemic draws) that one strategy beats the other on a given metric
is ≥ 0.90, and **undetermined** between 0.10 and 0.90. Thresholds are
conventions fixed here, before any result.

- **H1 supported** if, in at least one pre-registered set and scenario, the
  ranking of strategies by EV differs from their ranking by median or by CVaR
  5 %, or if EV > 0 while P(loss) > 0.5 for Strategy A.
- **H2 supported** if a comparison that is decisive at the posterior mean of
  the pull rates becomes undetermined, or reverses, once epistemic
  uncertainty is propagated.
- **H3 supported** if the advantage of A over B in EV (E1) or in
  P(K < a(c\*)) (E2) decreases from the gross to the net scenario, with a 95 %
  interval of the change excluding 0.
- **H4 supported** if the decisive winner differs between at least two sets, or
  between at least two price snapshot dates. With a single set and a single
  snapshot, H4 is reported as **not testable**.

Every hypothesis is reported as supported, not supported, or not testable,
with the evidence.

### 7.1 Comparability

Same budget and reference date; same currency, card conditions and fee
convention; acquisition and liquidation prices separated; same holding horizon
(or clearly distinct scenarios); central and adverse scenarios defined before
analysis; no parameter chosen because it makes a strategy win.

### 7.2 Minimum robustness tests

1. Replace mean price by median of available observations.
2. Apply a liquidity haircut to indicative prices.
3. Vary selling and shipping fees.
4. Widen pull-rate uncertainty or use CI bounds.
5. Exclude extreme cards / jackpots and recompute EV.
6. Compare several sets if data allows.
7. Vary the number of simulations and check metric stability.

Added in S1:

8. Prior sensitivity (Jeffreys vs uniform).
9. Exclude pull-rate rows with reconstructed counts or "estimated" confidence.
10. Liquidity haircuts anchored on observed sell-through and time-to-sale
    figures (Heck et al. 2026), clearly labelled as transferred evidence.

## 8. Paper structure

| Section | Content | Figures / tables |
|---|---|---|
| Abstract | Question, data, method, main result, main limitation. | n/a |
| 1. Introduction | Context, question, interest, contribution, plan. | Optional concept diagram. |
| 2. Literature review | Collectibles, pricing, pull-rate estimation, risk/liquidity. | Literature comparison table. |
| 3. Data | Sets, cards, pull rates, prices, costs, exclusions, licences. | Table 1 coverage & quality. |
| 4. Methodology | Slots, probability model, uncertainty, Monte Carlo, net price. | Equations, pipeline diagram. |
| 5. Experimental design | Budget, strategies A/B, scenarios, metrics, seeds, versions. | Table 2 parameters. |
| 6. Results | EV, median, P(loss), quantiles, CVaR, break-even. | Histograms, CDFs, sensitivity curves. |
| 7. Robustness | CIs, alternative prices, fees, liquidity, jackpot exclusion. | Tornado plot, Table 4. |
| 8. Discussion | Interpretation, limits, implications, non-generalisation. | No new results. |
| 9. Conclusion | Cautious answer, contribution, future work. | n/a |
| Appendix | Sources, definitions, tests, parameters, implementation. | Technical tables. |

### Figures and tables

| ID | Element | Shows |
|---|---|---|
| Fig. 1 | Data and simulation architecture | Traceability source → model → result |
| Fig. 2 | Slot structure of the selected booster | Collation assumptions |
| Fig. 3 | Value distribution of one opening | Dispersion, skewness, jackpots |
| Fig. 4 | CDF of net profit by strategy | Probability of exceeding a profit/loss threshold |
| Fig. 5 | P(loss) vs booster price | Risk thresholds |
| Fig. 6 | Break-even vs pull-rate assumptions | Sensitivity to uncertainty |
| Fig. 7 | EV and CVaR by strategy | Mean vs extreme risk |
| Tab. 1 | Data coverage and quality | Size, dates, provenance, limits |
| Tab. 2 | Simulation parameters | Reproducibility |
| Tab. 3 | Central results by set/scenario | Synthetic comparison |
| Tab. 4 | Robustness and sensitivity | Stability of conclusions |

## 9. Reproducibility plan

- Every experiment is a versioned YAML config in `research/experiments/`.
- Raw data is immutable; transformations are code, and tested.
- Results carry data snapshot ID, model version, seed, date and parameters.
- Paper figures are generated by scripts, never edited by hand.
- A redistributable toy dataset lets tests run without API keys.
- If snapshots cannot legally be shared, publish scripts and instructions, not the data.
- Cite sources, versions, licences and access dates.

## 10. Publishability criteria (Gate G8)

| Criterion | GO if… | NO-GO if… |
|---|---|---|
| Question | Precise, falsifiable, non-trivial. | The paper only describes the app. |
| Data | Traceable, comparable, legally usable. | Price data ambiguous or not allowed. |
| Method | Justified and validated model. | Monte Carlo without explicit model. |
| Results | Robust, quantified limits. | Conclusion hinges on one fragile rate or price. |
| Novelty | Explicitly compared to the literature. | Re-implementation of an existing calculator. |
| Reproducibility | Code, parameters, seeds, figures reproducible. | Manual, untraceable results. |

## 11. Grading extension (post-MVP)

Keep three notions separate: (1) graded population by grade, (2) share of PSA 10
among graded copies, (3) probability that a given raw copy gets PSA 10. Only (3)
answers a raw buyer's question, and it requires pre-submission condition
variables and a well-documented submission sample. A visual estimate is never
presented as equivalent to a PSA grading.

## 12. Defence questions

1. What exactly is your scientific contribution beyond the website?
2. What are the pull-rate sources and why is their sample credible?
3. How do you handle structural differences between boosters and sets?
4. Why this prior, and how do results change with another one?
5. What is the difference between listing price, aggregated price and realised sale?
6. How do you turn an observed price into a net realisable value?
7. Why compare strategies at identical budget and horizon?
8. What are the main selection and survivorship biases?
9. Which conclusions hold in adverse scenarios?
10. Which conclusions can you not draw from your data?

*If the data cannot answer the question cleanly, the right scientific result is
to say so.*
