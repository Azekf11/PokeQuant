from __future__ import annotations

import math
from datetime import UTC, datetime

import numpy as np
import pytest

from pokequant_core.booster import LAYOUTS, REVERSE, build_pools, build_set_posterior
from pokequant_core.ids import make_printing_id
from pokequant_core.model import p_hit
from pokequant_core.schemas import CardPrinting, PullRateObservation

NOW = datetime(2026, 1, 1, tzinfo=UTC)
# Synthetic set "zz": rarity -> (number of cards, variants of each card)
SPEC = {
    "common": (6, ("normal", "reverse")),
    "uncommon": (4, ("normal", "reverse")),
    "rare": (3, ("holo", "reverse")),
    "double rare": (2, ("holo",)),
    "ultra rare": (2, ("holo",)),
    "illustration rare": (2, ("holo",)),
    "special illustration rare": (1, ("holo",)),
    "hyper rare": (1, ("holo",)),
}
RATES = {  # rarity -> (hits, packs)
    "double rare": (170, 1000),
    "ultra rare": (65, 1000),
    "illustration rare": (80, 1100),
    "special illustration rare": (12, 1050),
    "hyper rare": (6, 1000),
}


def printings(spec: dict[str, tuple[int, tuple[str, ...]]] = SPEC) -> list[CardPrinting]:
    out, n = [], 0
    for rarity, (count, variants) in spec.items():
        for _ in range(count):
            n += 1
            for v in variants:
                out.append(
                    CardPrinting(
                        printing_id=make_printing_id("en", "zz", str(n), v),
                        card_id=f"zz-{n}",
                        set_id="zz",
                        number=str(n),
                        name=f"Card {n}",
                        rarity=rarity,
                        variant=v,
                        language="en",
                        source="test",
                        fetched_at=NOW,
                    )
                )
    return out


def rates(values: dict[str, tuple[int, int]] = RATES) -> list[PullRateObservation]:
    return [
        PullRateObservation(
            set_id="zz",
            scope="pack",
            rarity=rarity,
            hits=hits,
            packs=packs,
            rate=hits / packs,
            ci_low=0.0,
            ci_high=1.0,
            confidence="high",
            counts_reconstructed=True,
            dataset_ids=("T-1",),
            source="test",
            source_version="t",
            source_url="https://example.org",
        )
        for rarity, (hits, packs) in values.items()
    ]


def test_pools_use_base_printing_and_collect_reverses() -> None:
    pools = build_pools(printings())
    assert len(pools["common"]) == 6 and all(p.endswith(":normal") for p in pools["common"])
    assert all(p.endswith(":holo") for p in pools["rare"])
    assert len(pools[REVERSE]) == 6 + 4 + 3


def test_central_layout_places_every_rarity_and_sums_to_one() -> None:
    post = build_set_posterior("zz", printings(), rates(), LAYOUTS["tcgplayer"])
    assert set(post.posteriors) == {"rev2", "rare"}  # no ACE SPEC cards: rev1 deterministic
    assert post.posteriors["rev2"].outcomes == (
        "hyper rare",
        "illustration rare",
        "special illustration rare",
        REVERSE,
    )
    model = post.mean_model()
    assert model.n_cards_per_pack == 10
    for slot in model.slots:
        assert math.isclose(math.fsum(slot.outcomes.values()), 1.0)
    # n_rev2 = min packs = 1000: SIR pseudo-count 12/1050*1000
    expected = (12 / 1050 * 1000 + 0.5) / (1000 + 4 * 0.5)
    sir = model.cards_by_rarity["special illustration rare"][0]
    assert p_hit(model, sir) == pytest.approx(expected)


def test_alternative_layout_moves_hyper_rare_to_the_rare_slot() -> None:
    post = build_set_posterior("zz", printings(), rates(), LAYOUTS["hyper-in-rare-slot"])
    assert "hyper rare" in post.posteriors["rare"].outcomes
    assert "hyper rare" not in post.posteriors["rev2"].outcomes


def test_epistemic_draws_are_valid_and_vary() -> None:
    post = build_set_posterior("zz", printings(), rates(), LAYOUTS["tcgplayer"], weight=0.5)
    models = post.sample_models(np.random.default_rng(7), 50)
    dr = [m.slots[-1].outcomes["double rare"] for m in models]
    assert len(models) == 50 and len(set(dr)) == 50
    assert np.mean(dr) == pytest.approx(0.17, abs=0.02)


def test_registry_rarity_without_slot_is_rejected() -> None:
    extra = rates({**RATES, "shiny rare": (5, 1000)})
    with pytest.raises(ValueError, match="no slot"):
        build_set_posterior("zz", printings(), extra, LAYOUTS["tcgplayer"])


def test_catalogue_rarity_without_rate_is_rejected() -> None:
    partial = rates({k: v for k, v in RATES.items() if k != "hyper rare"})
    with pytest.raises(ValueError, match="no pull rate"):
        build_set_posterior("zz", printings(), partial, LAYOUTS["tcgplayer"])


def test_empty_residual_pool_is_rejected() -> None:
    no_uncommon = {k: v for k, v in SPEC.items() if k != "uncommon"}
    with pytest.raises(ValueError, match="uncommon"):
        build_set_posterior("zz", printings(no_uncommon), rates(), LAYOUTS["tcgplayer"])
