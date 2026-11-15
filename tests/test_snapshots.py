"""Committed raw snapshots must match the checksums of the manifest (immutability)."""

import hashlib
from pathlib import Path
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "manifests" / "snapshots.yaml"


def _files() -> list[tuple[Path, str]]:
    manifest: dict[str, Any] = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    return [
        (ROOT / snap["path"] / f["name"], f["sha256"])
        for snap in manifest["snapshots"]
        for f in snap["files"]
    ]


@pytest.mark.parametrize(("path", "sha256"), _files(), ids=lambda v: getattr(v, "name", ""))
def test_snapshot_checksum(path: Path, sha256: str) -> None:
    assert hashlib.sha256(path.read_bytes()).hexdigest() == sha256
