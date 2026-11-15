# 0005: Set selection rule

- Status: accepted
- Date: 2026-11-15

## Context

The protocol (§3.1) requires 1–3 sets chosen by a data-coverage audit, with a
rule written **before** prices are inspected. This ADR is committed before the
Poké Life snapshot and the catalogue are analysed, and before any price value
is looked at. Price *coverage* (whether a card has a price at all) is used;
price *values* are not.

## Decision

A set is **eligible** if all of the following hold:

1. English-language set present in the Poké Life registry snapshot.
2. Scarlet & Violet series or later (released 2023 or later): single
   10-card booster format whose pack composition is publicly documented.
3. At least 5 000 packs measured (maximum of `packs` over the set's rarity rows).
4. Every rarity row from "Double Rare" upwards has a non-missing `hits`,
   `packs` and confidence interval.
5. Catalogue complete in TCGdex: every card number of the main set is present
   with a rarity.
6. Price coverage: at least 90 % of cards of rarity "Rare" and above have at
   least one non-missing price field in TCGdex (any provider, any type).

Eligible sets are **ranked** lexicographically by:

1. share of rarity rows with `counts_reconstructed = FALSE` (higher first);
2. share of rarity rows with confidence `high` (higher first);
3. packs measured (higher first);
4. release date (older first, for a more settled market).

The **top 3** are selected (fewer if fewer are eligible). The ranking is
computed by a script from the snapshot, not by hand.

If no set is eligible, criterion 6 is relaxed to 75 %, then criterion 3 to
2 000 packs, each relaxation recorded in the data audit report.

## Consequences

- The choice is reproducible from the snapshot and cannot be steered by price
  results.
- Japanese sets and pre-2023 sets are out of the main analysis.
