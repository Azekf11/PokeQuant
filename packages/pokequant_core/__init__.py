"""PokéQuant core engine.

Probabilistic booster models, pull-rate uncertainty, Monte Carlo simulation,
valuation and risk metrics. See ``docs/ROADMAP.md`` for the build order.
"""

from importlib.metadata import version

__version__ = version("pokequant")

__all__ = ["__version__"]
