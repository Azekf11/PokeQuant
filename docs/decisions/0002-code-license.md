# 0002 — Code licence

- Status: accepted
- Date: 2026-11-14

## Context

The Definition of Done (§8.4) requires an explicit code licence (MIT or
Apache-2.0), distinct from data licences.

## Decision

- Code: **MIT**. Simplest permissive licence, widely accepted by journals and
  software venues; no patent-grant need identified for this project.
- Data: each dataset keeps its own licence, recorded in
  `data/manifests/sources.yaml`. The MIT licence does **not** apply to
  third-party data.
- The manuscript's licence (e.g. CC BY 4.0) is decided at submission time.

## Consequences

Switching to Apache-2.0 later is possible while the author is the only
copyright holder.
