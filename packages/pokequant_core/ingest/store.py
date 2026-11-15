"""Deterministic Parquet storage and DuckDB views for processed data.

Records are sorted by their primary key before writing, so the same inputs
always produce byte-identical files (idempotent imports).
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq
from pydantic import BaseModel


def write_records(
    records: Sequence[BaseModel], key: Callable[[Any], tuple[Any, ...]], path: Path
) -> str:
    """Sort by key and write Parquet; return the file's SHA-256.

    Keys must be unique (checked beforehand by ``validate``).
    """
    rows = [r.model_dump(mode="python") for r in sorted(records, key=key)]
    for row in rows:
        for name, value in row.items():
            if isinstance(value, tuple):
                row[name] = list(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pylist(rows)
    pq.write_table(table, path, compression="zstd", write_statistics=False)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def connect(processed_dir: Path) -> duckdb.DuckDBPyConnection:
    """In-memory DuckDB with one view per Parquet file of ``processed_dir``."""
    con = duckdb.connect()
    for file in sorted(processed_dir.glob("*.parquet")):
        literal = str(file).replace("'", "''")
        con.execute(f"CREATE VIEW {file.stem} AS SELECT * FROM read_parquet('{literal}')")
    return con
