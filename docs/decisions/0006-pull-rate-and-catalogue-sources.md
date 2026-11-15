# 0006: Pull-rate and catalogue sources

- Status: accepted
- Date: 2026-11-15

## Context

S1 audited nine sources (`data/manifests/sources.yaml`). S2 needs a pull-rate
source and a catalogue source, and must decide what raw data may be committed.

## Decision

1. **Pull rates: Poké Life registry**, dated version 2026-11-13, committed
   under `data/raw/pokelife/2026-11-13/` (CC BY 4.0 permits redistribution
   with attribution). The folder is allow-listed in `.gitignore`; checksums and
   attribution are in `data/manifests/snapshots.yaml`.
   `evidence.json` has no dated URL: it was fetched from the latest URL on
   2026-11-15 and is identified by its checksum only.
2. **Catalogue: TCGdex** (database under MIT). Pokémon TCG API is not used
   (deprecated, offline on 2027-03-01, no licence).
3. **TCGdex raw responses are not committed.** They contain price fields and
   image URLs whose rights are unclear (S1). They are cached locally under
   `data/raw/tcgdex/<date>/` (git-ignored) and can be re-fetched by
   `scripts/audit_sets.py`. A catalogue extract without prices may be
   committed later (S3) once the schema exists.

## Consequences

- Anyone can reproduce the pull-rate side of the study from the repository.
- The catalogue side is reproducible by re-fetching; TCGdex may change over
  time, so the S3 ingestion pipeline records fetch dates and checksums.
