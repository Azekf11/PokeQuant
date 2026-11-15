from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest

from pokequant_core.ingest.http import (
    USER_AGENT,
    CachedClient,
    SourceUnavailableError,
    meta_path,
    read_cached,
)

NOW = datetime(2026, 1, 2, tzinfo=UTC)
URL = "https://api.example/v2/thing"


class Recorder:
    """A mock transport that replays scripted responses and records requests."""

    def __init__(self, *responses: httpx.Response | Exception) -> None:
        self.responses = list(responses)
        self.requests: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        item = self.responses.pop(0) if len(self.responses) > 1 else self.responses[0]
        if isinstance(item, Exception):
            raise item
        return item


def client(recorder: Recorder, sleeps: list[float], **kwargs: object) -> CachedClient:
    return CachedClient(
        transport=httpx.MockTransport(recorder),
        sleep=sleeps.append,
        clock=lambda: NOW,
        **kwargs,  # type: ignore[arg-type]
    )


def test_fetch_writes_raw_and_sidecar_then_serves_cache(tmp_path: Path) -> None:
    rec, sleeps = Recorder(httpx.Response(200, json={"a": 1})), list[float]()
    path = tmp_path / "raw" / "thing.json"
    with client(rec, sleeps) as c:
        first = c.get_json(URL, path)
        second = c.get_json(URL, path)
    assert first.data == second.data == {"a": 1}
    assert len(rec.requests) == 1  # second call served from disk
    assert rec.requests[0].headers["User-Agent"] == USER_AGENT
    meta = json.loads(meta_path(path).read_text())
    assert meta["url"] == URL and meta["sha256"] == first.sha256
    assert second.fetched_at == NOW


def test_offline_without_cache_is_unavailable(tmp_path: Path) -> None:
    rec: Recorder = Recorder(httpx.Response(200, json={}))
    with client(rec, [], offline=True) as c, pytest.raises(SourceUnavailableError):
        c.get_json(URL, tmp_path / "x.json")
    assert rec.requests == []


def test_retries_with_backoff_then_succeeds(tmp_path: Path) -> None:
    rec = Recorder(httpx.Response(503), httpx.ConnectTimeout("slow"), httpx.Response(200, json=[1]))
    sleeps: list[float] = []
    with client(rec, sleeps, min_interval=0.5) as c:
        assert c.get_json(URL, tmp_path / "x.json").data == [1]
    assert sleeps == [1.0, 2.0, 0.5]


def test_source_unavailable_after_retries_and_nothing_cached(tmp_path: Path) -> None:
    rec = Recorder(httpx.Response(500))
    path = tmp_path / "x.json"
    with client(rec, [], retries=2) as c, pytest.raises(SourceUnavailableError):
        c.get_json(URL, path)
    assert len(rec.requests) == 3
    assert not path.exists()


def test_invalid_json_counts_as_failure(tmp_path: Path) -> None:
    rec = Recorder(httpx.Response(200, content=b"<html>"))
    with client(rec, [], retries=0) as c, pytest.raises(SourceUnavailableError):
        c.get_json(URL, tmp_path / "x.json")


def test_circuit_breaker_stops_calling_a_failing_source(tmp_path: Path) -> None:
    rec = Recorder(httpx.Response(500))
    with client(rec, [], retries=0, max_consecutive_failures=2) as c:
        for i in range(2):
            with pytest.raises(SourceUnavailableError):
                c.get_json(f"{URL}/{i}", tmp_path / f"{i}.json")
        with pytest.raises(SourceUnavailableError, match="circuit open"):
            c.get_json(f"{URL}/2", tmp_path / "2.json")
    assert len(rec.requests) == 2


def test_tampered_cache_is_rejected(tmp_path: Path) -> None:
    rec = Recorder(httpx.Response(200, json={"a": 1}))
    path = tmp_path / "x.json"
    with client(rec, []) as c:
        c.get_json(URL, path)
    path.write_text('{"a": 2}')
    with pytest.raises(ValueError, match="checksum"):
        read_cached(path)
