"""Booster model of one set from the processed tables (research/protocol/model_spec.md).

A layout lists the slots of a pack. A slot either always draws from one pool
(Commons, Uncommons) or draws one of several *hit* rarities with estimated
probabilities and a *residual* pool otherwise. Pools hold printing IDs, so a
card's reverse printing and its base printing are distinct outcomes.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field

import numpy as np

from pokequant_core.estimation import JEFFREYS, DirichletPosterior, slot_posterior
from pokequant_core.model import BoosterModel, Slot
from pokequant_core.schemas import CardPrinting, PullRateObservation

COMMON, UNCOMMON, RARE = "common", "uncommon", "rare"
REVERSE = "reverse"  # pool of every reverse-holo printing of the set
ACE_SPEC, DOUBLE_RARE, ULTRA_RARE = "ace spec rare", "double rare", "ultra rare"
ILLUSTRATION_RARE, SIR, HYPER_RARE = (
    "illustration rare",
    "special illustration rare",
    "hyper rare",
)
LOW_RARITIES = (COMMON, UNCOMMON)


@dataclass(frozen=True)
class SlotSpec:
    slot_id: str
    residual: str  # pool drawn when no hit rarity is drawn
    hits: tuple[str, ...] = ()


@dataclass(frozen=True)
class Layout:
    name: str
    slots: tuple[SlotSpec, ...]
    assumptions: tuple[str, ...] = field(default=())

    @property
    def hit_rarities(self) -> set[str]:
        return {r for s in self.slots for r in s.hits}


_BASE_SLOTS = (
    *(SlotSpec(f"c{i}", COMMON) for i in range(1, 5)),
    *(SlotSpec(f"u{i}", UNCOMMON) for i in range(1, 4)),
)
_ASSUMPTIONS = (
    "A-EQ: printings equally likely within a pool",
    "A-IND: slots independent",
    "A-REV: rev1 and rev2 share the reverse pool",
    "A-CU: Commons and Uncommons of one pack are distinct cards",
    "A-GOD: no special collation",
)

LAYOUTS: dict[str, Layout] = {
    # Central: TCGplayer pull-rate articles (model_spec §2).
    "tcgplayer": Layout(
        "tcgplayer",
        (
            *_BASE_SLOTS,
            SlotSpec("rev1", REVERSE, (ACE_SPEC,)),
            SlotSpec("rev2", REVERSE, (ILLUSTRATION_RARE, SIR, HYPER_RARE)),
            SlotSpec("rare", RARE, (DOUBLE_RARE, ULTRA_RARE)),
        ),
        ("A-HR: Hyper Rare in rev2", *_ASSUMPTIONS),
    ),
    # Robustness R12: Hyper Rare in the rare slot (PokeBeach, 2023).
    "hyper-in-rare-slot": Layout(
        "hyper-in-rare-slot",
        (
            *_BASE_SLOTS,
            SlotSpec("rev1", REVERSE, (ACE_SPEC,)),
            SlotSpec("rev2", REVERSE, (ILLUSTRATION_RARE, SIR)),
            SlotSpec("rare", RARE, (DOUBLE_RARE, ULTRA_RARE, HYPER_RARE)),
        ),
        ("R12: Hyper Rare in the rare slot", *_ASSUMPTIONS),
    ),
}


def build_pools(printings: Iterable[CardPrinting]) -> dict[str, list[str]]:
    """Pools of printing IDs: one per rarity (base printing) plus the reverse pool."""
    by_card: dict[str, dict[str, CardPrinting]] = {}
    for p in printings:
        by_card.setdefault(p.card_id, {})[p.variant] = p
    pools: dict[str, list[str]] = {}
    for variants in by_card.values():
        any_printing = next(iter(variants.values()))
        preferred = (
            ("normal", "holo") if any_printing.rarity in LOW_RARITIES else ("holo", "normal")
        )
        base = next((variants[v] for v in preferred if v in variants), None)
        if base is not None:
            pools.setdefault(base.rarity, []).append(base.printing_id)
        if "reverse" in variants:
            pools.setdefault(REVERSE, []).append(variants["reverse"].printing_id)
    return {name: sorted(ids) for name, ids in sorted(pools.items())}


@dataclass(frozen=True)
class SetPosterior:
    """Posterior over the slot probabilities of one set under one layout."""

    set_id: str
    layout: Layout
    pools: dict[str, list[str]]
    posteriors: dict[str, DirichletPosterior]  # random slots only
    prior: float
    weight: float

    def model(self, probabilities: Mapping[str, Sequence[float]]) -> BoosterModel:
        """Booster model with the given probabilities for each random slot."""
        slots = []
        for spec in self.layout.slots:
            post = self.posteriors.get(spec.slot_id)
            if post is None:
                slots.append(Slot(slot_id=spec.slot_id, outcomes={spec.residual: 1.0}))
                continue
            values = [float(v) for v in probabilities[spec.slot_id]]
            slots.append(
                Slot(slot_id=spec.slot_id, outcomes=dict(zip(post.outcomes, values, strict=True)))
            )
        return BoosterModel(
            product_id="booster-en",
            set_id=self.set_id,
            version=f"model_spec-v1/{self.layout.name}",
            cards_by_rarity=self.pools,
            slots=slots,
            assumptions=list(self.layout.assumptions),
        )

    def mean_model(self) -> BoosterModel:
        return self.model(
            {sid: [post.mean[o] for o in post.outcomes] for sid, post in self.posteriors.items()}
        )

    def sample_models(self, rng: np.random.Generator, size: int) -> list[BoosterModel]:
        """``size`` epistemic draws; each slot's Dirichlet is sampled independently."""
        draws = {sid: post.sample(rng, size) for sid, post in self.posteriors.items()}
        return [self.model({sid: d[i] for sid, d in draws.items()}) for i in range(size)]


def build_set_posterior(
    set_id: str,
    printings: Iterable[CardPrinting],
    pull_rates: Iterable[PullRateObservation],
    layout: Layout,
    *,
    prior: float = JEFFREYS,
    weight: float = 1.0,
) -> SetPosterior:
    """Combine catalogue pools and registry rates of one set into slot posteriors.

    Every registry rarity must belong to one slot of the layout, and every hit
    rarity of the layout that has cards in the catalogue must have a registry
    row; a hit rarity absent from both (e.g. ACE SPEC in sv10) is dropped.
    """
    pools = build_pools(p for p in printings if p.set_id == set_id)
    rates = {
        o.rarity: (o.hits, o.packs) for o in pull_rates if o.set_id == set_id and o.scope == "pack"
    }
    unplaced = set(rates) - layout.hit_rarities
    if unplaced:
        raise ValueError(f"{set_id}: registry rarities {sorted(unplaced)} have no slot")
    posteriors = {}
    for spec in layout.slots:
        if spec.residual not in pools:
            raise ValueError(f"{set_id}: pool {spec.residual!r} of slot {spec.slot_id} is empty")
        missing = [r for r in spec.hits if r in pools and r not in rates]
        if missing:
            raise ValueError(f"{set_id}: no pull rate for {missing} (slot {spec.slot_id})")
        observed = {r: rates[r] for r in spec.hits if r in rates}
        if observed:
            posteriors[spec.slot_id] = slot_posterior(
                observed, spec.residual, prior=prior, weight=weight
            )
    return SetPosterior(set_id, layout, pools, posteriors, prior, weight)
