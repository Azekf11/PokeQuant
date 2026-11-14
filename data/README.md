# Data

| Folder | Content | In git? |
|---|---|---|
| `raw/` | Source snapshots exactly as received, one folder per source and date (`raw/<source>/<YYYY-MM-DD>/`), with SHA-256 checksums. Never modified. | Only if the licence allows redistribution — each allowed source is allow-listed explicitly in `.gitignore` after an ADR. |
| `processed/` | Normalised Parquet files produced by the ingestion pipeline from `raw/`. Always regenerable. | No |
| `manifests/` | Provenance: source register (`sources.yaml`), licences, access dates, snapshot checksums, versions. | Yes |

Rules (see the [project charter](../docs/PROJECT_CHARTER.md#data-policy)):

- Every observation records source, URL, UTC timestamp, version, currency,
  language, condition/grade and collection method.
- No price without a date; no rate without a sample size or confidence level.
- Access right ≠ redistribution right. When in doubt, do not commit the data:
  store identifiers and links to the source only.
- Tests never depend on this folder; they use the synthetic toy dataset in
  `tests/fixtures/`.
