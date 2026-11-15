"""Vectorised Monte Carlo engine for booster openings (protocol §4.3, model_spec).

A ``BoosterModel`` is compiled once into integer arrays; packs are then drawn
slot by slot for many runs at a time. Only per-pack *values* are accumulated,
never the full list of cards, so memory stays linear in the number of packs.

Card values are supplied by the caller as one number per printing (e.g. the
liquidation value l(c) of S6), or as a matrix with one column per cost scenario:
every column is then valued on the same simulated openings (common random
numbers). The engine itself knows nothing about prices.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from pokequant_core.model import BoosterModel

FloatArray = NDArray[np.float64]
IntArray = NDArray[np.int64]
DISTINCT_GROUPS = (("c1", "c2", "c3", "c4"), ("u1", "u2", "u3"))  # assumption A-CU


@dataclass(frozen=True)
class CompiledSlot:
    slot_id: str
    probs: FloatArray  # P(outcome k), sums to 1
    pools: tuple[IntArray, ...]  # printing indices of each outcome's pool


@dataclass(frozen=True)
class CompiledModel:
    printing_ids: tuple[str, ...]
    slots: tuple[CompiledSlot, ...]
    distinct_groups: tuple[tuple[int, ...], ...]  # slot positions drawn without replacement

    def index(self, printing_id: str) -> int:
        return self.printing_ids.index(printing_id)


def compile_model(
    model: BoosterModel,
    distinct_groups: Sequence[Sequence[str]] = DISTINCT_GROUPS,
    multiplicity: Mapping[str, int] | None = None,
) -> CompiledModel:
    """Integer arrays of ``model``.

    ``multiplicity`` gives a printing that many entries in its pool instead of
    one, so that printings of one pool can have unequal weights (robustness
    R11; the default is assumption A-EQ). Pool probabilities are unchanged.
    """
    printing_ids = tuple(sorted({p for pool in model.cards_by_rarity.values() for p in pool}))
    position = {p: i for i, p in enumerate(printing_ids)}
    weight = dict(multiplicity or {})
    unknown = set(weight) - set(position)
    if unknown or any(w < 1 for w in weight.values()):
        raise ValueError(f"bad multiplicity: unknown {sorted(unknown)} or weight < 1")
    pool_arrays = {
        name: np.array([position[p] for p in pool for _ in range(weight.get(p, 1))], dtype=np.int64)
        for name, pool in model.cards_by_rarity.items()
    }
    slots = []
    for slot in model.slots:
        outcomes = [(r, p) for r, p in slot.outcomes.items() if p > 0]
        probs = np.array([p for _, p in outcomes], dtype=np.float64)
        slots.append(
            CompiledSlot(
                slot.slot_id, probs / probs.sum(), tuple(pool_arrays[r] for r, _ in outcomes)
            )
        )
    slot_pos = {s.slot_id: i for i, s in enumerate(slots)}
    groups = tuple(
        tuple(slot_pos[s] for s in group)
        for group in distinct_groups
        if all(s in slot_pos for s in group)
    )
    return CompiledModel(printing_ids, tuple(slots), groups)


def _draw_slot(slot: CompiledSlot, rng: np.random.Generator, n: int) -> IntArray:
    """Printing index drawn in this slot for ``n`` packs."""
    if len(slot.pools) == 1:
        pool = slot.pools[0]
        return pool[rng.integers(0, len(pool), n)]
    outcome = np.searchsorted(np.cumsum(slot.probs), rng.random(n), side="right")
    outcome = np.minimum(outcome, len(slot.pools) - 1)  # guard against rounding at 1.0
    out = np.empty(n, dtype=np.int64)
    for k, pool in enumerate(slot.pools):
        mask = outcome == k
        out[mask] = pool[rng.integers(0, len(pool), int(mask.sum()))]
    return out


def open_packs(cm: CompiledModel, rng: np.random.Generator, n: int) -> IntArray:
    """Printing indices of ``n`` packs, shape (n, n_slots).

    Slots of a distinct group (A-CU) are redrawn until the pack holds no
    duplicate within the group.
    """
    cards = np.column_stack([_draw_slot(s, rng, n) for s in cm.slots])
    for group in cm.distinct_groups:
        cols = list(group)
        while True:
            sub = np.sort(cards[:, cols], axis=1)
            dup = np.any(sub[:, 1:] == sub[:, :-1], axis=1)
            if not dup.any():
                break
            rows = np.flatnonzero(dup)
            for c in cols:
                cards[rows, c] = _draw_slot(cm.slots[c], rng, len(rows))
    return cards


def pack_values(
    cm: CompiledModel, values: FloatArray, rng: np.random.Generator, n: int, chunk: int = 200_000
) -> FloatArray:
    """Total value of each of ``n`` packs, shape (n,) or (n, k) for k value columns."""
    _check_values(cm, values)
    out = np.empty((n, *values.shape[1:]), dtype=np.float64)
    for start in range(0, n, chunk):
        stop = min(start + chunk, n)
        out[start:stop] = values[open_packs(cm, rng, stop - start)].sum(axis=1)
    return out


def _check_values(cm: CompiledModel, values: FloatArray) -> None:
    if values.ndim not in (1, 2) or values.shape[0] != len(cm.printing_ids):
        raise ValueError("need one value (row) per printing of the compiled model")


def slot_card_probabilities(cm: CompiledModel) -> FloatArray:
    """P(printing i in slot s), shape (n_slots, n_printings); rows sum to 1."""
    out = np.zeros((len(cm.slots), len(cm.printing_ids)))
    for s, slot in enumerate(cm.slots):
        for p, pool in zip(slot.probs, slot.pools, strict=True):
            np.add.at(out[s], pool, p / len(pool))
    return out


def sum_pack_values(
    cm: CompiledModel,
    values: FloatArray,
    rng: np.random.Generator,
    n_packs: IntArray,
    chunk_runs: int = 20_000,
) -> FloatArray:
    """Total value of ``n_packs[j]`` packs for each run j, without listing the cards.

    For each slot, the number of copies of every printing across a run's packs
    is multinomial; the total is those counts times ``values``. Exact for
    independent slots drawn with replacement (it ignores A-CU, whose effect is
    checked numerically in the validation report).
    """
    _check_values(cm, values)
    probs = slot_card_probabilities(cm)
    n_packs = np.asarray(n_packs, dtype=np.int64)
    out = np.zeros((len(n_packs), *values.shape[1:]))
    for lo in range(0, len(n_packs), chunk_runs):
        m = n_packs[lo : lo + chunk_runs]
        for row in probs:
            support = np.flatnonzero(row)
            counts = rng.multinomial(m, row[support] / row[support].sum())
            out[lo : lo + chunk_runs] += counts @ values[support]
    return out


def values_vector(cm: CompiledModel, values: Mapping[str, float]) -> FloatArray:
    """Value array aligned on the compiled printings; every printing must be priced."""
    missing = [p for p in cm.printing_ids if p not in values]
    if missing:
        raise ValueError(f"{len(missing)} printing(s) without value, e.g. {missing[:3]}")
    return np.array([values[p] for p in cm.printing_ids], dtype=np.float64)


# --- E1: budget liquidation -------------------------------------------------


def simulate_e1(
    cm: CompiledModel,
    values: FloatArray,
    rng: np.random.Generator,
    *,
    n_packs: int,
    booster_cost: float | FloatArray,
    runs: int,
    exact_packs: bool = False,
) -> FloatArray:
    """Net profit of ``runs`` openings of ``n_packs`` packs: sum of values - n * b.

    ``exact_packs`` draws every card (with A-CU); the default aggregate path is
    exact in distribution without A-CU and much faster.
    """
    if n_packs < 1 or runs < 1:
        raise ValueError("need at least one pack and one run")
    if exact_packs:
        per_pack = pack_values(cm, values, rng, runs * n_packs)
        totals = per_pack.reshape(runs, n_packs, *values.shape[1:]).sum(axis=1)
    else:
        totals = sum_pack_values(cm, values, rng, np.full(runs, n_packs, dtype=np.int64))
    return totals - n_packs * np.asarray(booster_cost, dtype=np.float64)


# --- E2: target acquisition --------------------------------------------------


@dataclass(frozen=True)
class TargetSplit:
    """A model split around one target printing (slots independent, A-IND)."""

    p_hit: float  # P(target in one pack)
    without: CompiledModel  # a pack conditioned on not containing the target
    hit_slot: int  # the only slot that can contain the target
    target: int  # printing index of the target in ``cm``


def split_on_target(cm: CompiledModel, printing_id: str) -> TargetSplit:
    target = cm.index(printing_id)
    slots, hit_slots, q_hit = [], [], 0.0
    for i, slot in enumerate(cm.slots):
        q = sum(
            p * np.count_nonzero(pool == target) / len(pool)
            for p, pool in zip(slot.probs, slot.pools, strict=True)
        )
        if q == 0:
            slots.append(slot)
            continue
        hit_slots.append(i)
        q_hit = float(q)
        new_probs, new_pools = [], []
        for p, pool in zip(slot.probs, slot.pools, strict=True):
            kept = pool[pool != target]
            mass = p * len(kept) / len(pool)
            if len(kept) and mass > 0:
                new_probs.append(mass)
                new_pools.append(kept)
        probs = np.array(new_probs) / sum(new_probs)
        slots.append(CompiledSlot(slot.slot_id, probs, tuple(new_pools)))
    if len(hit_slots) != 1:
        raise ValueError(f"target must be drawable in exactly one slot (found {len(hit_slots)})")
    without = CompiledModel(cm.printing_ids, tuple(slots), cm.distinct_groups)
    return TargetSplit(q_hit, without, hit_slots[0], target)


def simulate_e2(
    cm: CompiledModel,
    values: FloatArray,
    rng: np.random.Generator,
    *,
    target: str,
    booster_cost: float | FloatArray,
    target_price: float | FloatArray,
    n_max: int,
    runs: int,
) -> tuple[FloatArray, IntArray]:
    """Net cost K of acquiring ``target`` by opening, and packs opened, per run.

    Packs are opened until the first copy of the target (at most ``n_max``);
    every other card is liquidated at ``values``. If the cap is reached, the
    target is bought at ``target_price``. Exact under slot independence: packs
    before the hit are drawn conditionally on not containing the target; the
    hit pack has the target in its slot and unconditional other slots.
    """
    split = split_on_target(cm, target)
    k = np.minimum(rng.geometric(split.p_hit, runs), n_max + 1)  # n_max + 1 = no hit
    hit = k <= n_max
    misses = np.where(hit, k - 1, n_max).astype(np.int64)
    # Packs without the target: a variable number per run.
    other_value = sum_pack_values(split.without, values, rng, misses)
    # The hit pack: every slot but the hit slot is unconditional.
    n_hit = int(hit.sum())
    if n_hit:
        cards = open_packs(cm, rng, n_hit)
        cards[:, split.hit_slot] = split.target
        hit_value = values[cards].sum(axis=1) - values[split.target]
        other_value[hit] += hit_value
    opened = np.where(hit, k, n_max)
    shape = (runs,) + (1,) * (values.ndim - 1)  # broadcast over value columns
    b = np.asarray(booster_cost, dtype=np.float64)
    a = np.asarray(target_price, dtype=np.float64)
    cost = opened.reshape(shape) * b - other_value + np.where(hit.reshape(shape), 0.0, a)
    return cost, opened
