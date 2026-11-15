# SSRN submission sheet

Ready-to-paste fields for the SSRN form. Every number comes from
`research/reports/results.md` and `research/reports/robustness.md`.

## Title

Opening or Buying? A Probabilistic and Risk-Adjusted Comparison of Pokémon TCG Booster Acquisition and Secondary-Market Purchases

## Author

Anh-Vu TA, Independent Researcher

## Date written

November 15, 2026

## Abstract (1580 characters)

Is opening Pokémon Trading Card Game booster packs a competitive way to acquire cards, compared with buying them directly on the secondary market? We model three recent English sets (Stellar Crown, Surging Sparks and Destined Rivals) slot by slot. Rarity rates come from community openings, with Dirichlet posteriors, and a nested Monte Carlo propagates their uncertainty (200 posterior draws × 20,000 runs). Cards are valued at TCGplayer market prices in USD on 2026-11-15, converted into net realisable values under three cost scenarios. Hypotheses, metrics, decision rules and robustness tests were pre-registered before any result existed.

Under the central scenario, opening loses money on average for every set and budget. The break-even booster price is 1.03 to 1.42 USD against a retail price of 4.49 USD, and 3.44 to 4.29 USD without any fee, shipping or haircut. Opening 36 boosters loses 111 to 125 USD on average. Buying cards directly also loses money through round-trip costs, but less than half as much, and it is decisively better on the mean, the median and the 5 % conditional value-at-risk in 35 of 36 budget comparisons. Opening until a set's most valuable card appears is cheaper than buying it in only 4 % to 14 % of simulated runs. Opening's average loss and the advantage of buying hold in all sixteen pre-registered robustness variants. Liquidation assumptions change the size of the gap; pull-rate assumptions barely do. Code, configurations, the pull-rate snapshot and all derived results are public, and one command regenerates every table and figure.

## Keywords

trading card games, loot boxes, Monte Carlo simulation, Bayesian
uncertainty, conditional value-at-risk, pre-registration, reproducibility

## JEL classification

- D12: Consumer Economics: Empirical Analysis
- D81: Criteria for Decision-Making under Risk and Uncertainty
- C15: Statistical Simulation Methods: General
- L83: Sports; Gambling; Restaurants; Recreation; Tourism
- Z11: Economics of the Arts and Literature

## Suggested networks

- Economics Research Network (ERN): Microeconomics, consumer behaviour
- Econometrics / statistics (simulation methods)

## Links

- Code, data and configurations: https://github.com/Azekf11/PokeQuant
- DOI (all versions): https://doi.org/10.5281/zenodo.24251050
- Interactive demo: https://azekf11.github.io/PokeQuant/

## File

`research/paper/paper.pdf` (release v1.0.2)
