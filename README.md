# PokéQuant

**Opening or buying?** A reproducible, probabilistic and risk-adjusted
comparison of Pokémon TCG booster opening versus direct purchase on the
secondary market.

> **Status: week 0 — repository bootstrap.** No data has been collected and no
> result has been computed yet. See the [roadmap](docs/ROADMAP.md).

## Research question

To what extent is opening Pokémon TCG boosters an economically competitive
acquisition strategy compared with buying cards directly on the secondary
market, once pull-rate uncertainty, value dispersion, fees and liquidity are
taken into account?

The project does not try to prove that boosters are or are not profitable. It
measures under which conditions, and with what uncertainty, the strategies
differ — reporting the full distribution (median, probability of loss,
quantiles, CVaR), not only the expected value.

Details: [research protocol](research/protocol/protocol.md) ·
[project charter](docs/PROJECT_CHARTER.md).

## Planned deliverables

1. `pokequant_core` — a Python engine: slot-based booster model, pull-rate
   uncertainty, Monte Carlo simulation, valuation and risk metrics.
2. A data ingestion pipeline with a provenance manifest for every source.
3. Validation and robustness reports.
4. A working paper whose figures all regenerate from this repository.
5. A minimal web interface to explore scenarios.

## Repository layout

```
packages/pokequant_core/   Python engine (importable package)
tests/                     Automated tests
data/                      raw/ (immutable snapshots) · processed/ · manifests/ (provenance, licences)
research/protocol/         Research protocol, model specification
research/                  experiments/, reports/, paper/ are added in the week that needs them
docs/                      Roadmap, project charter, decision log (ADRs)
```

## Getting started

Requires [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/Azekf11/PokeQuant.git
cd PokeQuant
uv sync                 # create the environment from uv.lock
uv run pre-commit install
make check              # lint + format check + types + tests
```

## Data and licences

- Code: [MIT](LICENSE).
- Third-party data keeps its own licence and is listed in
  `data/manifests/sources.yaml` (from week 1). Data that may not be
  redistributed is **never** committed; the repository then ships the import
  scripts and a synthetic toy dataset instead.
- No marketplace scraping and no circumvention of API terms or quotas.

## Disclaimer

PokéQuant is an independent research project. It is **not affiliated with,
endorsed or sponsored by** The Pokémon Company, Nintendo, Creatures or
Game Freak. Pokémon and related names are trademarks of their respective
owners.

Results are experimental analyses for educational and research purposes. They
are **not financial or investment advice**.

## Contributing and citation

See [CONTRIBUTING.md](CONTRIBUTING.md) for the workflow and
[CITATION.cff](CITATION.cff) to cite the software.
