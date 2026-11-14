# 0004 — Publication route

- Status: accepted
- Date: 2026-11-14

## Context

The final goal is a personal research publication. The author is an
independent researcher without prior arXiv submissions. Lead times for
endorsement and review are outside our control, so the route is fixed in S1
(roadmap amendment A8).

Facts checked on 2026-11-14:

- **arXiv.** Since January 2026, arXiv requires first-time submitters in every
  category to be endorsed by an established author of that category; an
  institutional e-mail alone is no longer enough
  ([arXiv blog, Dec 2025](https://blog.arxiv.org/arxiv/2025/12/10/updated-endorsement-policy-for-arxiv-mathematics),
  [arXiv endorsement help](https://info.arxiv.org/help/endorsement.html)).
  Exact rules for q-fin / stat.AP are confirmed in the submission flow itself.
- **Zenodo.** With the GitHub integration, every GitHub release is archived and
  receives a version DOI plus a concept DOI. If a `.zenodo.json` exists it
  overrides `CITATION.cff`. Published records cannot be deleted.
- **JOSS** (software paper). Current criteria expect at least six months of
  public development history with releases, issues/PRs and ideally external use
  ([review criteria](https://joss.readthedocs.io/en/latest/review_criteria.html)).
  A repository created in Nov 2026 is not eligible before ~May 2027.
- **SSRN.** Free working-paper deposit, no endorsement step.

## Decision

1. **Software:** GitHub release `v1.0.0` archived on Zenodo (DOI) in S12.
   Test the integration on the Zenodo sandbox first. Keep `CITATION.cff` as the
   single metadata source (no `.zenodo.json`) unless Zenodo needs extra fields.
2. **Working paper:** deposit on **SSRN** (guaranteed route) in S12, with the
   Zenodo DOI of the exact code version.
3. **arXiv (q-fin.GN or stat.AP):** in parallel, look for an endorser from S8
   onward (authors of references in our bibliography who are active on arXiv).
   No endorsement → SSRN + Zenodo only; this does not block the project.
4. **Peer review (after S12):** submit the working paper to a journal that fits
   the final result (applied statistics, consumer economics, or
   cultural-economics venues), chosen once the results are known.
5. **JOSS:** possible from ~May 2027 if the software has had real public use.

## Consequences

- The publication never depends on a single gatekeeper.
- The author's real name and (optionally) ORCID must be added to
  `CITATION.cff` before the Zenodo release.
