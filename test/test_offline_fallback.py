"""Test the offline stale-cache fallback in download_cache.get_file().

These tests are fully hermetic: they monkeypatch ``requests`` so no network
access is made. The point of the feature is to keep readabs working offline
(e.g. on a plane) by falling back to previously cached data, so - fittingly -
these tests can themselves be run with no internet connection.
"""

import re
from collections.abc import Callable, Generator
from contextlib import contextmanager, redirect_stdout
from hashlib import sha256
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

import requests

import readabs.download_cache as dc

# --- constants
URL = "https://www.abs.gov.au/fake/6202001.xlsx"
MISSING_URL = "https://www.abs.gov.au/fake/never-cached.xlsx"
CACHED_BYTES = b"STALE CACHED CONTENT"
PAST = "Wed, 01 Jan 2020 00:00:00 GMT"  # older than any freshly written cache file
FUTURE = "Fri, 01 Jan 2100 00:00:00 GMT"  # newer than the cache - forces a download


# --- helpers
class _FakeResponse:
    """Minimal stand-in for a requests.Response from a HEAD request."""

    def __init__(self, status_code: int = 200, last_modified: str | None = None) -> None:
        self.status_code = status_code
        self.headers: dict[str, str] = {}
        if last_modified is not None:
            self.headers["Last-Modified"] = last_modified


def _cache_path(cache_dir: Path, url: str, cache_prefix: str = "cache") -> Path:
    """Reproduce the cache file path that get_file() computes for a URL."""
    hash_name = sha256(url.encode("utf-8")).hexdigest()
    tail_name = url.rsplit("/", 1)[-1].split("?", 1)[0]
    file_name = re.sub(dc.BAD_CACHE_PATTERN, "", f"{cache_prefix}--{hash_name}--{tail_name}")
    return cache_dir / file_name


@contextmanager
def _patched_requests(
    head: Callable[..., object] | None = None,
    get: Callable[..., object] | None = None,
) -> Generator[None, None, None]:
    """Swap requests.head/requests.get for the duration of the block, then restore.

    Works under pytest and when the module is run directly, without relying on
    the pytest monkeypatch fixture.
    """
    orig_head, orig_get = requests.head, requests.get
    if head is not None:
        requests.head = head  # type: ignore[assignment]
    if get is not None:
        requests.get = get  # type: ignore[assignment]
    try:
        yield
    finally:
        requests.head = orig_head  # type: ignore[assignment]
        requests.get = orig_get  # type: ignore[assignment]


def _no_internet(url: str, **_kwargs: object) -> object:
    """Simulate an unreachable network by raising a ConnectionError."""
    raise requests.exceptions.ConnectionError(f"Network is unreachable for {url}")


def _must_not_be_called(url: str, **_kwargs: object) -> object:
    """Fail the test if the network is touched when the cache should have been used."""
    msg = f"the network should not have been used for {url}"
    raise AssertionError(msg)


def _head_with(last_modified: str) -> Callable[..., _FakeResponse]:
    """Build a fake HEAD that reports the given Last-Modified time, ignoring its args."""

    def _head(*_args: object, **_kwargs: object) -> _FakeResponse:
        return _FakeResponse(200, last_modified)

    return _head


# --- tests
def test_offline_returns_stale_cache() -> None:
    """Offline + cache present -> returns the cached bytes with a stale warning."""
    with TemporaryDirectory() as tmp:
        cache_dir = Path(tmp)
        _cache_path(cache_dir, URL).write_bytes(CACHED_BYTES)

        captured = StringIO()
        with _patched_requests(head=_no_internet), redirect_stdout(captured):
            result = dc.get_file(URL, cache_dir=cache_dir)

        assert result == CACHED_BYTES
        warning = captured.getvalue()
        assert "may be out of date" in warning
        assert URL in warning


def test_offline_no_cache_raises() -> None:
    """Offline + no cache -> raises HttpError (cannot do anything useful)."""
    with TemporaryDirectory() as tmp:
        cache_dir = Path(tmp)
        raised = False
        try:
            with _patched_requests(head=_no_internet):
                dc.get_file(MISSING_URL, cache_dir=cache_dir)
        except dc.HttpError:
            raised = True
        assert raised, "expected HttpError when offline with no cached copy"


def test_offline_no_cache_ignore_errors() -> None:
    """Offline + no cache + ignore_errors -> returns empty bytes instead of raising."""
    with TemporaryDirectory() as tmp:
        cache_dir = Path(tmp)
        with _patched_requests(head=_no_internet):
            result = dc.get_file(MISSING_URL, cache_dir=cache_dir, ignore_errors=True)
        assert result == b""


def test_fresh_cache_not_redownloaded() -> None:
    """Server copy older than cache -> cache used without any GET request."""
    with TemporaryDirectory() as tmp:
        cache_dir = Path(tmp)
        _cache_path(cache_dir, URL).write_bytes(CACHED_BYTES)

        with _patched_requests(head=_head_with(PAST), get=_must_not_be_called):
            result = dc.get_file(URL, cache_dir=cache_dir)
        assert result == CACHED_BYTES


def test_download_failure_falls_back_to_cache() -> None:
    """Server reports a newer copy but the GET fails -> fall back to stale cache."""
    with TemporaryDirectory() as tmp:
        cache_dir = Path(tmp)
        _cache_path(cache_dir, URL).write_bytes(CACHED_BYTES)

        # server claims a much newer copy (a download is attempted), but the GET dies
        with _patched_requests(head=_head_with(FUTURE), get=_no_internet):
            result = dc.get_file(URL, cache_dir=cache_dir)
        assert result == CACHED_BYTES


if __name__ == "__main__":
    test_offline_returns_stale_cache()
    test_offline_no_cache_raises()
    test_offline_no_cache_ignore_errors()
    test_fresh_cache_not_redownloaded()
    test_download_failure_falls_back_to_cache()
    print("All offline-fallback tests passed.")
