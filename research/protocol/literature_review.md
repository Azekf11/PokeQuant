# Literature review — working notes (S1)

Bibliography: [`research/paper/references.bib`](../paper/references.bib)
(40 verified entries). Each entry's `note` says what was actually read. As of
2026-11-15 three texts were read in full: Heck et al. (2026), and preprint
versions of Acerbi & Tasche (2002) and Gordy & Juneja (2010). Everything else
is abstract-level. **No claim in the paper may rest on an abstract we have not
checked against the full text.**

## 1. Closest prior work

| Reference | What it does | Overlap with PokéQuant | Read |
|---|---|---|---|
| Mota (2026), *Valuation Framework for Sealed Products…* | EV of sealed Magic: The Gathering products vs sealed price; "sealed-opened spread" as a no-arbitrage condition; discusses costs, variance and liquidity conceptually. | **Closest method.** Different game; hypothetical numerical example, no real data; slot probabilities treated as known (Bayesian treatment left to future work, §9.2); no tail risk; no comparison with buying singles. Introduces a minimum-value threshold and a per-card liquidity factor, both close to our cost model. | full text |
| Danz (2026), Princeton senior thesis | Hedonic pricing over ~4.77 M observations, 138 sets (2023–2026); scarcity vs character traits; sealed vs raw segmentation; weak-form efficiency. | Same market; no booster or pull-rate model in the abstract. | landing page (restricted) |
| Baro (2026), SSRN | Log-linear hedonic model of PSA 10 prices for 360 SIR/IR cards (eBay sales). R² ≈ 0.88; PSA 10 / raw elasticity ≈ 0.48. | Graded valuation only. Linked to a commercial product: not independent. | abstract |
| Sharma (2026), SSRN | Grading premium by segment (vintage/modern × grail/ordinary), 2020–2022 boom-bust. | Grading only; warns against a fixed graded/raw multiplier. | abstract |
| Heck et al. (2026), PLOS ONE | One-year field study of 300 Pokémon cards listed on eBay: 73 % sold; median price €1.95; holos sell in median 17 days vs 78 for others; posted prices act as a ceiling. | **Direct input for liquidity scenarios** (haircut on bulk, time to sale). | full text (partial) |

## 2. Practitioner tools (what is *not* new)

| Tool | Does | Missing |
|---|---|---|
| TCGTalk guides | Slot EV + Monte Carlo (100k runs): win rate, median P/L, P5/P95, histogram. | Fixed pull rates (no epistemic uncertainty), no fees/liquidity, no CVaR, qualitative comparison with singles. |
| PokemonPriceTracker EV guide | EV = Σ price × rate with a flat 0.85 friction haircut. | EV only; price type unspecified. |
| RipIndex | EV/price ratio, P(one card > pack price). | No distribution, fees or uncertainty. |
| PackRip | Slot EV from a price snapshot; notes median ≪ EV. | No simulation or fees. |

**Consequence:** a pack-level Monte Carlo distribution is not a contribution by
itself. Neither is "EV is misleading because of skew" (H1) — it is already
stated informally by practitioners; our value is to quantify it with net prices
and uncertainty.

## 3. Axes of the review

- **Collectibles as assets:** Burton & Jacobsen 1999 (survey); Dimson &
  Spaenjers 2011 (stamps; costs matter); Dobrynskaya & Kishilova 2022 (LEGO);
  Dobrynskaya & Strelnikov 2025 (CS:GO skins, items from loot boxes); Mei &
  Moses 2002 (art); Wang & Langelett (sealed CCG boxes); Hilbert 2024.
- **Hedonic pricing:** Rosen 1974; Renneboog & Spaenjers 2013; Hughes 2022
  (rarity designation — measured by pack odds — carries its own price premium
  in MTG: links pull rates to prices); Mullin & Dunn 2002.
- **Loot boxes / gacha / booster packs:** Chen et al. 2021 (loot box design);
  Gan 2021; Hu, Qin & Sekar 2024 (rarity design of blind boxes); Zendle et al.
  2021 (physical booster packs as loot-box analogues); Xiao et al. 2023 (poor
  odds disclosure — supports estimating rates instead of trusting published
  ones); Xiao et al. 2025.
- **Risk and estimation:** Artzner et al. 1999; Rockafellar & Uryasev 2000,
  2002; Acerbi & Tasche 2002 (ES coherent for discrete distributions — our
  payoffs are discrete); Brown, Cai & DasGupta 2001 (Jeffreys/Wilson intervals);
  Jeffreys 1946; Gordy & Juneja 2010 (outer/inner budget in nested
  simulation); Der Kiureghian & Ditlevsen 2009 (aleatory vs epistemic).
- **Liquidity and listed vs realised prices:** Einav et al. 2018; Katkar &
  Reiley 2006 (Pokémon cards on eBay); Lucking-Reiley et al. 2007; Bajari &
  Hortaçsu 2004; Heck et al. 2026.
- **Grading / certification (extension only):** Jin & Kato 2006; Jin, Kato &
  List 2010; Dranove & Jin 2010; Lizzeri 1999.

## 4. Provisional novelty statement

> Prior academic work on Pokémon cards studies price determinants, grading
> premiums, market efficiency and liquidity; practitioner tools compute pack EV
> and, in some cases, simulated outcome distributions with fixed pull rates.
> The closest formal treatment (Mota 2026) defines a sealed-opened spread for
> Magic: The Gathering. To our knowledge, no study combines, for the Pokémon
> TCG, (i) Bayesian uncertainty on community-estimated pull rates propagated
> through a nested Monte Carlo, (ii) typed market prices converted into net
> realisable values with explicit fees and liquidity scenarios, (iii) coherent
> tail-risk measures, and (iv) two pre-registered estimands — equal-budget
> liquidation and the cost of acquiring a target card — compared with direct
> purchase.

**Status: provisional.** It must be re-checked once the full texts below are read.

## 5. To do before freezing the novelty claim

- [x] Read Mota (2026) in full — closest work (SSRN PDF, 14 pages, read
      2026-11-15). The novelty claim holds; §2.4 of the paper now states what
      the two models share.
- [ ] Read Baro (2026) and Sharma (2026) in full (SSRN).
- [ ] Danz (2026) is restricted: ask the author for a copy.
- [ ] Finish the Discussion of Heck et al. (2026).
- [ ] Read in full at least the core method references used in §4 of the paper:
      Acerbi & Tasche 2002, Rockafellar & Uryasev 2002, Brown et al. 2001,
      Gordy & Juneja 2010. *2026-11-15: Acerbi & Tasche (arXiv preprint v5)
      and Gordy & Juneja (FEDS working paper 2008-21) read in full; the two
      others are still abstract or landing page only.*
