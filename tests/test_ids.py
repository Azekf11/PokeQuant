"""Canonical identifiers (ADR 0008)."""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from pokequant_core.ids import (
    PrintingKey,
    make_printing_id,
    normalise_rarity,
    parse_printing_id,
)


def test_known_example() -> None:
    assert make_printing_id("en", "sv08", "001", "reverse") == "en:sv08:001:reverse"


@pytest.mark.parametrize(
    ("language", "set_id", "number", "variant"),
    [
        ("EN", "sv08", "001", "normal"),  # language must be lower-case ISO 639-1
        ("en", "sv08", "0:1", "normal"),  # separator inside a component
        ("en", "", "001", "normal"),
        ("en", "sv08", "001", "firstEdition"),  # unsupported variant
    ],
)
def test_invalid_components_rejected(language: str, set_id: str, number: str, variant: str) -> None:
    with pytest.raises(ValueError):
        make_printing_id(language, set_id, number, variant)


def test_parse_rejects_wrong_shape() -> None:
    with pytest.raises(ValueError):
        parse_printing_id("en:sv08:001")


@given(
    st.sampled_from(["en", "ja", "fr"]),
    st.from_regex(r"[a-z]{2,4}[0-9]{0,2}(\.[0-9a-z]{1,2})?", fullmatch=True),
    st.from_regex(r"[A-Za-z0-9]{1,5}", fullmatch=True),
    st.sampled_from(["normal", "reverse", "holo"]),
)
def test_round_trip(language: str, set_id: str, number: str, variant: str) -> None:
    pid = make_printing_id(language, set_id, number, variant)
    assert parse_printing_id(pid) == PrintingKey(language, set_id, number, variant)


def test_number_padding_is_preserved() -> None:
    assert parse_printing_id("en:sv10:007:holo").number == "007"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Double Rare", "double rare"),
        ("Double rare", "double rare"),
        (" ACE SPEC Rare ", "ace spec rare"),
    ],
)
def test_rarity_normalisation(raw: str, expected: str) -> None:
    assert normalise_rarity(raw) == expected
