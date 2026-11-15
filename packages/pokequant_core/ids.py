"""Canonical identifiers (ADR 0008).

``printing_id = "{language}:{set_id}:{number}:{variant}"``, e.g. ``en:sv08:001:reverse``.
Condition and grade are *not* part of the identifier; they belong to each
price observation.
"""

from __future__ import annotations

import re
from typing import Literal, NamedTuple, get_args

Variant = Literal["normal", "reverse", "holo"]
VARIANTS: frozenset[str] = frozenset(get_args(Variant))

_LANGUAGE = re.compile(r"[a-z]{2}")
_SET_ID = re.compile(r"[a-z0-9][a-z0-9.\-]*")
_NUMBER = re.compile(r"[A-Za-z0-9]+")


class PrintingKey(NamedTuple):
    language: str
    set_id: str
    number: str
    variant: str


def make_printing_id(language: str, set_id: str, number: str, variant: str) -> str:
    """Build a canonical printing ID, validating every component."""
    if not _LANGUAGE.fullmatch(language):
        raise ValueError(f"language must be a lower-case ISO 639-1 code, got {language!r}")
    if not _SET_ID.fullmatch(set_id):
        raise ValueError(f"invalid set_id {set_id!r}")
    if not _NUMBER.fullmatch(number):
        raise ValueError(f"invalid card number {number!r}")
    if variant not in VARIANTS:
        raise ValueError(f"unsupported variant {variant!r}; expected one of {sorted(VARIANTS)}")
    return f"{language}:{set_id}:{number}:{variant}"


def parse_printing_id(printing_id: str) -> PrintingKey:
    """Split and validate a canonical printing ID."""
    parts = printing_id.split(":")
    if len(parts) != 4:
        raise ValueError(f"printing_id must have 4 ':'-separated parts, got {printing_id!r}")
    key = PrintingKey(*parts)
    make_printing_id(*key)  # validates each component
    return key


def normalise_rarity(rarity: str) -> str:
    """Canonical rarity label: trimmed and case-folded ("Double Rare" -> "double rare")."""
    return " ".join(rarity.split()).casefold()
