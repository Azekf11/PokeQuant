# Scoping note: end of S1

Date: 2026-11-15. Deliverable of roadmap week S1 ("note de cadrage + registre
des sources").

## 1. What S1 established

| Topic | Result | Where |
|---|---|---|
| Research question, Q1–Q5, H1–H4 | Kept; hypotheses now have explicit decision rules. | [`protocol.md`](protocol.md) §1, §7.0b |
| Estimands | Split into **E1** (equal-budget liquidation) and **E2** (cost of acquiring a target card). | `protocol.md` §6.3 |
| Metrics | Formal definitions and sign conventions (VaR/CVaR reported as positive losses, α = 5 %). | `protocol.md` §7.0 |
| Literature | 40 verified references; closest work is Mota (2026, MTG) and practitioner Monte Carlo tools. Novelty = combination, not simulation per se. | [`literature_review.md`](literature_review.md) |
| Data sources | 9 sources audited. | [`data/manifests/sources.yaml`](../../data/manifests/sources.yaml) |
| Publication | Zenodo DOI + SSRN guaranteed; arXiv needs an endorser. | [ADR 0004](../../docs/decisions/0004-publication-route.md) |

## 2. Data situation

- **Pull rates: available and redistributable.** Poké Life registry, CC BY
  4.0, immutable dated versions, per-rarity hits / packs / Jeffreys CI /
  confidence / reconstructed-count flag. 167 English sets; largest samples
  around 10 000–25 000 packs (e.g. Chilling Reign, Battle Styles, Destined
  Rivals, Surging Sparks). Caveats: mostly automated curation, some counts
  reconstructed or lower bounds.
- **Catalogue: available.** TCGdex (MIT database, no key, multilingual).
  Pokémon TCG API is deprecated (offline 2027-03-01): not used.
- **Prices: the main risk.** No price source can currently be redistributed
  without written permission. Usable for access: TCGdex price fields
  (TCGplayer USD, Cardmarket EUR; listing and provider-market types, rights
  unclear) and PkmnPrices (free tier, no licence granted). Realised sales
  (eBay sold) are not accessible through any open API.

### Options to prepare for Gate G2 (end of S2)

| Option | Price type | Reproducible by third parties? | Legal status |
|---|---|---|---|
| P1: TCGdex price fields, kept locally; publish only derived statistics + fetch scripts + snapshot hash | provider_market (+ listing) | Re-run on a new snapshot, not on ours | Unclear → ask TCGdex |
| P2: PkmnPrices with written permission | provider_market; sold if paid plan | Depends on permission | To request |
| P3: Small documented manual pilot of realised prices for the highest-value cards | sold | Partially (published sample if allowed) | To check per source |
| P4: Fallback: simulation study with price scenarios + limited case study | scenario | Fully | No risk |

Provider-market prices are not realised sales: whichever option is chosen, the
paper treats them as indicative and applies liquidity haircuts (Heck et al.
2026 provides empirical anchors for time to sale and sell-through of low-value
cards).

## 3. Open actions (owner: author)

1. Download and read the SSRN PDFs of Mota (2026), Baro (2026), Sharma (2026).
2. Ask T. Danz for a copy of the Princeton thesis.
3. Ask TCGdex about rights on its price fields and images.
4. Ask PkmnPrices whether derived statistics or a frozen snapshot may be published.
5. Review `protocol.md` v1; when satisfied, tag `prereg-v1` on `main`.

## 4. Exit criterion

"Question, hypotheses, scope and variables frozen." Met once the author has
reviewed `protocol.md` v1 and the `prereg-v1` tag exists. The novelty claim is
**not** part of the pre-registration; it stays provisional until the full texts
are read.
