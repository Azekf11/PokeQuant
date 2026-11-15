"""Polite, cached HTTP access to external sources.

Every successful response is written once to a raw snapshot folder, with a
sidecar ``<file>.meta.json`` recording URL, UTC fetch time and SHA-256. Raw
files are never overwritten: a cached file is always served from disk.

Failure handling: timeouts, retries with exponential backoff, and a simple
circuit breaker that stops calling a source after repeated consecutive
failures. ``offline=True`` serves only from the cache.
"""

from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

USER_AGENT = "PokeQuant-research/0.1 (+https://github.com/Azekf11/PokeQuant)"


class SourceUnavailableError(RuntimeError):
    """A source could not be reached (offline, circuit open, or repeated failures)."""


@dataclass(frozen=True)
class Fetched:
    data: Any
    fetched_at: datetime
    sha256: str
    url: str


def meta_path(path: Path) -> Path:
    return path.with_name(path.name + ".meta.json")


def read_cached(path: Path) -> Fetched:
    """Read a cached raw file and its sidecar metadata."""
    raw = path.read_bytes()
    meta = json.loads(meta_path(path).read_text(encoding="utf-8"))
    digest = hashlib.sha256(raw).hexdigest()
    if digest != meta["sha256"]:
        raise ValueError(f"raw file {path} does not match its recorded checksum")
    return Fetched(
        data=json.loads(raw),
        fetched_at=datetime.fromisoformat(meta["fetched_at"]),
        sha256=digest,
        url=meta["url"],
    )


def write_sidecar(path: Path, url: str, fetched_at: datetime, note: str | None = None) -> None:
    meta: dict[str, Any] = {
        "url": url,
        "fetched_at": fetched_at.astimezone(UTC).isoformat(),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }
    if note:
        meta["note"] = note
    meta_path(path).write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")


class CachedClient:
    def __init__(
        self,
        *,
        offline: bool = False,
        min_interval: float = 0.2,
        retries: int = 3,
        max_consecutive_failures: int = 5,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self.offline = offline
        self.min_interval = min_interval
        self.retries = retries
        self.max_consecutive_failures = max_consecutive_failures
        self._sleep = sleep
        self._clock = clock
        self._consecutive_failures = 0
        self._client = httpx.Client(
            headers={"User-Agent": USER_AGENT}, timeout=30, transport=transport
        )

    def __enter__(self) -> CachedClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self._client.close()

    def get_json(self, url: str, path: Path) -> Fetched:
        if path.exists():
            return read_cached(path)
        if self.offline:
            raise SourceUnavailableError(f"offline and not cached: {url}")
        if self._consecutive_failures >= self.max_consecutive_failures:
            raise SourceUnavailableError(f"circuit open after repeated failures; skipped {url}")

        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                response = self._client.get(url)
                response.raise_for_status()
                payload = response.json()
            except (httpx.HTTPError, ValueError) as error:
                last_error = error
                if attempt < self.retries:
                    self._sleep(2.0**attempt)
                continue
            self._consecutive_failures = 0
            fetched_at = self._clock()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(response.content)
            write_sidecar(path, url, fetched_at)
            self._sleep(self.min_interval)
            return Fetched(payload, fetched_at, hashlib.sha256(response.content).hexdigest(), url)

        self._consecutive_failures += 1
        raise SourceUnavailableError(f"{url} failed after {self.retries + 1} attempts") from (
            last_error
        )
