from importlib.metadata import version

import pokequant_core


def test_version_matches_distribution_metadata() -> None:
    assert pokequant_core.__version__ == version("pokequant")
