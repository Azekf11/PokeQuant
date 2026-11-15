# 0016: Mega Evolution sets and the slot of the Mega Hyper Rare (prereg-v5)

- Status: accepted
- Date: 2026-11-16
- Decided by: author
- Extends: [ADR 0015](0015-extension-to-eligible-sets-and-pull-rate-checks.md) (evaluability rule),
  [ADR 0011](0011-operational-comparison-rules.md), [ADR 0012](0012-operational-robustness-tests.md),
  model specification §2 (layout)
- Parameters: [research/experiments/mega_sets.yaml](../../research/experiments/mega_sets.yaml),
  [research/experiments/mega_sets_rare_slot.yaml](../../research/experiments/mega_sets_rare_slot.yaml)

## Context

ADR 0015 left out four eligible sets: Mega Evolution (me01), Phantasmal Flames
(me02), Chaos Rising (me04) and Pitch Black (me05). Their rarity "Mega Hyper
Rare" has no slot in the main layout, and no layout was invented for them.

**What the sources say** (read in a browser on 2026-11-16):

- **The four TCGplayer pull-rate articles of these sets** (P. Day).
  - Double Rare and Ultra Rare are "in the Rare slot".
  - Illustration Rare and Special Illustration Rare are "in the second Reverse
    Holo slot".
  - This is the main layout of model specification §2.
  - The Mega Evolution article says the Pokémon Company "did away with the
    Hyper Rare rarity and replaced it" with the Mega Hyper Rare.
  - None of the four articles names the slot of the Mega Hyper Rare.
- **Bulbapedia, *Booster pack (TCG)*.** Its international table applies
  "starting in Scarlet & Violet" and has the following content:
  - it places the Hyper Rare in the second reverse slot;
  - it lists the ACE SPEC Rare only from Temporal Forces to Prismatic
    Evolutions;
  - it does not list the Mega Hyper Rare.
- **PokéBeach (July 2025).** Mega Evolution packs still contain a Basic Energy
  card and a code card.

The slot of the Mega Hyper Rare is therefore not documented. Every other
rarity of the four sets maps to a documented slot.

**What was seen before this record.**
- The Poké Life registry rows (rates, counts, datasets) of the four sets.
- The pull-rate tables printed in the four TCGplayer articles.
- A PokéBeach article (September 2025) that quotes a market price range for
  the Mega Evolution Mega Hyper Rare cards. That range is a third-party
  statement, not a value of the price snapshot.
- After ingesting the four sets on 2026-11-16, only the row counts and the
  number of printings by rarity in the catalogue. No price value of the
  snapshot and no result for the four sets has been viewed.

## Decision

An **exploratory extension**, pre-registered under the tag `prereg-v5`. It
changes nothing in `analysis-v1` or in the ten-set extension. Its results are
reported in a separate subsection of the paper, with the layout assumption
stated.

1. **Sets.** me01, me02, me04 and me05. 30th Celebration stays out (ADR 0015).
2. **Central layout `mega-in-rev2` (assumption A-MHR).** The slots are those
   of the main layout, with two changes:
   - `rev1` is always a reverse-holo printing, since these sets have no ACE
     SPEC Rare;
   - the Mega Hyper Rare takes the place of the Hyper Rare among the hits of
     `rev2` (Illustration Rare, Special Illustration Rare, Mega Hyper Rare).

   The Hyper Rare is in `rev2` in the main layout (model specification §2),
   and TCGplayer states that the Mega Hyper Rare replaced it. The slot itself
   is an assumption.
3. **Paired alternative `mega-in-rare-slot` (M1).** Same layout, with the Mega
   Hyper Rare among the hits of the rare slot (Double Rare, Ultra Rare, Mega
   Hyper Rare) instead of `rev2`.
4. **Analysis.**
   - **Runs.** Both layouts are run with `mega_sets.yaml` and
     `mega_sets_rare_slot.yaml`. These are identical to `extension_sets.yaml`
     (tag `prereg-v4`) except name, description, sets, processed-data folder
     and layout. They use the same seed, prior, draws, runs, scenarios,
     estimands, price basis and snapshot.
   - **Checks.** C1–C3 of ADR 0012 and the break-even price b\* are reported
     by set under both layouts. A check is stated as holding for a set only
     if it holds under both.
   - **Hypotheses.** H1–H3 of ADR 0011 are reported for the four sets.
   - **H4 across sets.** H4 is reported over the four sets, and over the
     fourteen sets by pooling the per-set verdicts of this run with those of
     the ten-set run. A verdict depends only on its own set (ADR 0011 item 9).
     The central layout is used.
   - **Robustness tests.** Not repeated.
5. **Pull-rate checks** (as in ADR 0015, items 3 to 5).
   - **S1 (source check).** Each single-source registry row is compared with
     the rate printed in the set's TCGplayer article, at the printed
     precision. The printed values are committed in
     `research/reports/mega/tcgplayer_published_rates.csv`.
   - **F1 (duplicate flag).** The flag rule is applied unchanged, against the
     other thirteen sets.
   - **P1 (held-out predictive check).** For every pooled row, the TCGplayer
     counts predict the hits of the row's other datasets, pooled together.
     Holm correction is applied at family-wise level 0.05.
6. **Reporting.**
   - `research/reports/mega_sets.md`: C1–C3, b\*, H1–H4 under both layouts.
   - `research/reports/mega/pull_rate_checks.md`: S1, F1 and P1.
   - Card prices stay private (ADR 0009); only derived statistics are
     committed.

## Consequences

- H4 across sets is tested on fourteen sets.
- The one undocumented input, the slot of the Mega Hyper Rare, is bracketed
  by two layouts instead of being assumed silently. If a conclusion differs
  between the two, it is reported as not established.
- If a documented layout for the Mega Hyper Rare appears later, it replaces
  A-MHR only through a new ADR.
