"""Paper assembly: citations resolve against references.bib, unknown keys fail."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("build_paper", ROOT / "scripts/build_paper.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["build_paper"] = module
    spec.loader.exec_module(module)
    return module


def test_citations_resolve_to_author_year() -> None:
    bp = _load()
    bib = bp.parse_bib((ROOT / "research/paper/references.bib").read_text(encoding="utf-8"))
    cited: list[str] = []
    text = (
        "A [@jeffreys1946invariant]. B [-@heck2026sales]. "
        "C [@artzner1999coherent; @acerbi2002coherence]."
    )
    out = bp.resolve(text, bib, cited)
    assert "(Jeffreys 1946)" in out
    assert "B (2026)" in out
    assert "(Artzner et al. 1999; Acerbi and Tasche 2002)" in out
    assert cited == [
        "jeffreys1946invariant",
        "heck2026sales",
        "artzner1999coherent",
        "acerbi2002coherence",
    ]
    with pytest.raises(KeyError, match="unknown citation key"):
        bp.resolve("[@nobody2099]", bib, [])


def test_every_bib_entry_has_a_read_note() -> None:
    bp = _load()
    bib = bp.parse_bib((ROOT / "research/paper/references.bib").read_text(encoding="utf-8"))
    assert len(bib) >= 40
    for entry in bib.values():
        assert "read:" in entry.fields.get("note", ""), entry.key
