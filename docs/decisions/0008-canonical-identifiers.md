# 0008 — Canonical identifiers

- Status: accepted
- Date: 2026-11-15

## Context

The charter forbids merging two printings under an ambiguous identifier: set,
number, variant and language can change a card's value radically. Sources use
different identifiers (Poké Life `destined-rivals`, TCGdex `sv10`, TCGdex card
`sv10-001`, TCGplayer / Cardmarket product IDs).

## Decision

1. **`set_id`** = the TCGdex set ID (e.g. `sv08`). Other sources are mapped to
   it by exact, case-insensitive set-name match within the Scarlet & Violet and
   Mega Evolution series. An ambiguous match is an ingestion error; an
   unmatched set (out of scope, e.g. Sword & Shield) is excluded and listed in
   the ingestion report. Never a fuzzy guess.
2. **`printing_id`** = `"{language}:{set_id}:{number}:{variant}"`, e.g.
   `en:sv08:001:reverse`.
   - `language`: ISO 639-1 code (`en` only in the main analysis).
   - `number`: TCGdex `localId`, kept as a string with its zero padding.
   - `variant`: one of `normal`, `reverse`, `holo` (TCGdex variant flags).
     Other variants (`firstEdition`, `wPromo`) are rejected for now.
3. **Condition and grade are not part of `printing_id`.** They are attributes
   of each `PriceObservation` (`condition = "unspecified"` when the provider
   does not state it). The secondary unit of analysis of the charter
   (printing × condition) is therefore the pair (`printing_id`, `condition`).
4. **Provider price variants** map to printing variants as follows:
   - TCGplayer: `normal` → `normal`, `reverse-holofoil` → `reverse`,
     `holofoil` → `holo`; any other key is skipped and logged.
   - Cardmarket reports one product per card with plain fields and `-holo`
     fields. Plain fields → the card's base variant (`normal` if it exists,
     else `holo`). `-holo` fields → `reverse` when the card has both a `normal`
     and a `reverse` printing; otherwise they are **ambiguous** and skipped
     and logged.
5. Identifiers are validated by a single function (`pokequant_core.ids`) used
   by every adapter.

## Consequences

- Every price can be traced to exactly one printing, or is explicitly
  discarded with a reason.
- Adding Japanese sets later only changes the `language` component.
