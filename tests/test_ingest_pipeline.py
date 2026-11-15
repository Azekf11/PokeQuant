from __future__ import annotations

import json
from pathlib import Path

import pytest
from ingest_fixtures import CARDS, PL_VERSION, PULL_RATES_ROWS, SET, TD_VERSION, build_root
from test_ingest_tcgdex import fetched

from pokequant_core.cli import main
from pokequant_core.ingest import pipeline, tcgdex
from pokequant_core.ingest.http import CachedClient, SourceUnavailableError
from pokequant_core.ingest.store import connect
from pokequant_core.ingest.validate import Tables, ValidationError, check


def run(root: Path, sets: tuple[str, ...] = ("zz01",)) -> pipeline.IngestResult:
    with CachedClient(offline=True) as client:
        return pipeline.run(root, PL_VERSION, TD_VERSION, sets, client)


def snapshot_bytes(out: Path) -> dict[str, bytes]:
    return {p.name: p.read_bytes() for p in sorted(out.iterdir())}


def test_end_to_end_on_synthetic_snapshots(tmp_path: Path) -> None:
    result = run(build_root(tmp_path))
    m = result.manifest
    assert {k: v["rows"] for k, v in m["outputs"].items()} == {
        "sets": 1,
        "printings": 6,
        "pull_rates": 2,  # "Other Set" is in the catalogue but not selected
        "prices": 9,
    }
    assert m["pokelife_sets_outside_catalogue"] == ["elsewhere"]
    assert m["skipped"]["ambiguous '-holo' variant (ADR 0008)"] == 1
    assert m["skipped"]["unmapped TCGplayer variant"] == 1
    assert m["inputs"]["tcgdex"]["files"] == 6

    con = connect(result.out_dir)
    assert con.sql("select count(*) from prices where price_type = 'sold'").fetchall() == [(0,)]
    rows = con.sql("select rarity, cards_in_rarity from pull_rates order by rarity").fetchall()
    assert rows == [("double rare", 1), ("special illustration rare", 1)]


def test_import_is_idempotent(tmp_path: Path) -> None:
    root = build_root(tmp_path)
    first = snapshot_bytes(run(root).out_dir)
    second = snapshot_bytes(run(root).out_dir)
    assert first == second
    assert set(first) == {f"{t}.parquet" for t in Tables.__dataclass_fields__} | {"manifest.json"}


def test_registry_and_catalogue_disagreement_fails_validation(tmp_path: Path) -> None:
    rows = [PULL_RATES_ROWS[0].replace("Double Rare,1,", "Double Rare,2,"), *PULL_RATES_ROWS[1:]]
    root = build_root(tmp_path, rows)
    with pytest.raises(ValidationError, match="registry says 2 cards, catalogue has 1"):
        run(root)
    assert not pipeline.output_dir(root, PL_VERSION, TD_VERSION).exists()


def test_rarity_absent_from_catalogue_fails_validation(tmp_path: Path) -> None:
    rows = [PULL_RATES_ROWS[0].replace("Double Rare", "Mega Rare"), *PULL_RATES_ROWS[1:]]
    with pytest.raises(ValidationError, match="rarity absent"):
        run(build_root(tmp_path, rows))


def test_duplicates_and_dangling_prices_are_reported() -> None:
    parsed = tcgdex.parse_card(fetched(CARDS[0]))
    tables = Tables(
        sets=[tcgdex.parse_set(fetched(SET))],
        printings=parsed.printings * 2,
        pull_rates=[],
        prices=parsed.prices[:1],
    )
    errors = check(tables)
    assert any(e.startswith("printings: 2 duplicate") for e in errors)
    assert "pull_rates: no records" in errors
    dangling = check(Tables(tables.sets, [], [], parsed.prices[:1]))
    assert any(e.startswith("price for unknown printing") for e in dangling)


def test_mixed_currencies_on_one_venue_are_reported() -> None:
    parsed = tcgdex.parse_card(fetched(CARDS[0]))
    eur = next(p for p in parsed.prices if p.venue == "cardmarket")
    prices = [*parsed.prices, eur.model_copy(update={"currency": "USD", "statistic": "other"})]
    tables = Tables([tcgdex.parse_set(fetched(SET))], parsed.printings, [], prices)
    assert "prices: venue cardmarket mixes currencies ['EUR', 'USD']" in check(tables)


def test_missing_raw_file_offline_is_source_unavailable(tmp_path: Path) -> None:
    root = build_root(tmp_path)
    (root / "data/raw/tcgdex" / TD_VERSION / "cards/zz01-004.json").unlink()
    with pytest.raises(SourceUnavailableError, match="offline"):
        run(root)


def test_cli_reports_success_and_failure(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = build_root(tmp_path)
    args = ["ingest", "--pokelife", PL_VERSION, "--tcgdex", TD_VERSION, "--offline"]
    assert main([*args, "--sets", "zz01", "--root", str(root)]) == 0
    assert "prices" in capsys.readouterr().out
    assert main([*args, "--sets", "zz09", "--root", str(root)]) == 1
    assert "ingestion failed" in capsys.readouterr().err
    out = pipeline.output_dir(root, PL_VERSION, TD_VERSION)
    manifest = json.loads((out / "manifest.json").read_text())
    assert manifest["sets"] == ["zz01"]
