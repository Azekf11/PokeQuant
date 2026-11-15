<!-- Draft written in week S11. Sources of truth: data/manifests/, research/experiments/main.yaml, research/reports/validation.md. -->

# Appendix

## A. Sources and licences

| Input | Source and version | Licence or permission | In the replication package |
|---|---|---|---|
| Pull rates | Poké Life pull-rate evidence registry, version 2026-11-13, accessed 2026-11-15 | CC BY 4.0 | Yes: `data/raw/pokelife/2026-11-13/`, with SHA-256 checksums |
| Slot layout | TCGplayer pull-rate articles for the three sets (model specification, `research/protocol/model_spec.md`) | Facts cited with sources | Described, not copied |
| Catalogue | TCGdex API, fetched 2026-11-15 | MIT | Re-fetched by script; processed tables are rebuilt |
| Prices | TCGdex, relaying TCGplayer (USD) market prices, 2026-11-15 | Permission for this non-commercial project (ADR 0009) | No: only derived statistics; the fetch script and checksums are |
| Seller fees | TCGplayer seller fee page, read 2026-11-15 | Facts cited | In `research/experiments/main.yaml` |
| Liquidity evidence (R10) | Heck et al. [-@heck2026sales] | Open access article | Cited |

Prices are typed. The main analysis uses the provider *market* price, a
provider aggregate. Robustness test R1 uses the median of the listing
statistics (low, mid, high, direct low) and the market price, labelled as an
indicative estimate. No price is presented as a realised sale.

## B. Definitions

Π is the net profit of a run in USD.

- **E1:** Π = Σ ℓ(C_i) − n·b for opening n boosters at price b.
- **E2:** Π = a(c\*) − K, where K is the cost of opening until the target
  appears, net of the other cards sold.

A seller receives ℓ(c) = max(0, p(c)(1 − h)(1 − f_m − f_p) − f_0 − s). A
buyer pays a(c) = p(c)(1 + f_b) + s_b.

| Metric | Definition |
|---|---|
| Mean | E[Π] |
| Median | q₀.₅(Π) |
| P(loss) | P(Π < 0) |
| VaR 5 % | −q₀.₀₅(Π), a positive loss |
| CVaR 5 % | −E[Π \| Π ≤ q₀.₀₅(Π)]; estimator: minus the mean of the ⌈0.05 N⌉ smallest values |
| Break-even booster price | b\* = E[Σ ℓ(C_i)] for one booster: the mean of E1 is zero when b = b\* |
| P(K < a(c\*)) | Share of runs in which opening until the target was cheaper than buying it |
| Interval | 2.5 %–97.5 % quantiles of a metric over the 200 posterior draws |
| Monte Carlo error | Batch-means standard error within a draw, median over draws |
| Decisive | One strategy is better in at least 90 % of the posterior draws |

## C. Validation of the engine

`scripts/validate_engine.py` checks the engine against exact results, with
synthetic card values:

1. **Toy case.** A one-slot toy case gives a simulated mean 1.76 standard
   errors from the exact value, with N = 10⁶.
2. **Card frequencies.** Simulated card frequencies in the random slots of
   Surging Sparks pass a χ² test: p = 0.15, 0.64 and 0.54.
3. **Hit counts.** Hit counts for a Special Illustration Rare over 100 packs
   match the binomial in mean, variance and P(at least one).
4. **Error decay.** The root-mean-square error falls with a log-log slope of
   −0.52, against −0.5 in theory, from N = 10³ to 10⁶.
5. **Aggregate path.** The aggregate multinomial path agrees with
   card-by-card simulation (Kolmogorov–Smirnov p = 0.91).
6. **Packs to the target.** The capped number of packs to a target matches
   its closed form.
7. **Reproducibility.** The same seed, data and model give identical output.

The full report is `research/reports/validation.md`.

## D. Parameters

| Parameter | Value |
|---|---|
| Sets | Stellar Crown (sv07), Surging Sparks (sv08), Destined Rivals (sv10) |
| Product | One English booster pack; 10 modelled slots (layout `tcgplayer`) |
| Prior | Jeffreys (a₀ = ½), weight w = 1 on every registry row |
| Epistemic draws K | 200 |
| Aleatory runs M | 20,000 per draw (1,000 samples in the 5 % tail) |
| Seed | 20261115 (NumPy PCG64 via SeedSequence) |
| E1 budgets | 1, 10, 36, 100 boosters |
| E2 targets | Most expensive printing; most expensive Special Illustration Rare; cap n_max = ⌈3 / p_hit⌉ |
| Cost scenarios | Table in §5.2 (gross, central, adverse) |
| Decision threshold | 0.90 of posterior draws |
| Price date | 2026-11-15 (second snapshot for H4: 2026-12-13) |

## E. Reproduction

From a clone of the repository:

```bash
uv sync
make check        # lint, types and tests
make reproduce    # data, validation, main run, robustness, reports and figures
```

`make reproduce` needs the TCGdex responses in the local cache. They are
fetched by `pokequant ingest` without `--offline` on first use. It takes about
three hours on eight cores. Each run writes a manifest with the configuration
hash, seed, data snapshot identifiers and the SHA-256 of its results.
