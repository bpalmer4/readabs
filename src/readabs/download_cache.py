"""download_cache.py - a module for downloading and caching data from the web.

The default cache directory can be specified by setting the environment
variable READABS_CACHE_DIR.
"""

# system imports
import re
from datetime import UTC, datetime
from hashlib import sha256
from os import getenv, utime
from pathlib import Path
from typing import NotRequired, TypedDict, Unpack

# data imports
import pandas as pd
import requests

# --- constants
# define the default cache directory
DEFAULT_CACHE_DIR = "./.readabs_cache"
READABS_CACHE_DIR = getenv("READABS_CACHE_DIR", DEFAULT_CACHE_DIR)
READABS_CACHE_PATH = Path(READABS_CACHE_DIR)
GOOD_HTTP_CODES = {200, 201, 202, 204}  # HTTP codes considered successful

DOWNLOAD_TIMEOUT = 60  # seconds
HEAD_REQUEST_TIMEOUT = 20  # seconds
NANOSECONDS_PER_SECOND = 1_000_000_000  # conversion factor
BAD_CACHE_PATTERN = r'[~"#%&*:<>?\\{|}]+'  # chars to remove from cache filenames


class FileKwargs(TypedDict):
    """TypedDict for file-related keyword arguments."""

    verbose: NotRequired[bool]
    ignore_errors: NotRequired[bool]
    cache_only: NotRequired[bool]


# --- Exception classes
class HttpError(Exception):
    """A problem retrieving data from HTTP."""


class CacheError(Exception):
    """A problem retrieving data from the cache."""


# --- functions
def check_for_bad_response(
    url: str,
    response: requests.Response,
    **kwargs: Unpack[FileKwargs],
) -> bool:
    """Check HTTP response for errors and handle accordingly.

    Args:
        url: The URL that was requested
        response: The HTTP response object
        **kwargs: Optional parameters including 'ignore_errors' (bool)

    Returns:
        bool: True if there was a problem, False if response is OK

    Raises:
        HttpError: If there's a problem and ignore_errors is False

    """
    ignore_errors = kwargs.get("ignore_errors", False)
    code = response.status_code
    if code not in GOOD_HTTP_CODES:
        problem = f"Problem {code} accessing: {url}."
        if not ignore_errors:
            raise HttpError(problem)
        print(problem)
        return True

    return False


def request_get(
    url: str,
    **kwargs: Unpack[FileKwargs],
) -> bytes:
    """Download content from a URL using HTTP GET.

    Args:
        url: The URL to download from
        **kwargs: Optional parameters including 'verbose' and 'ignore_errors'

    Returns:
        bytes: The downloaded content, or empty bytes if error ignored

    Raises:
        HttpError: If download fails and ignore_errors is False

    """
    # Initialise variables
    verbose = kwargs.get("verbose", False)
    ignore_errors = kwargs.get("ignore_errors", False)

    if verbose:
        print(f"About to request/download: {url}")

    try:
        gotten = requests.get(url, allow_redirects=True, timeout=DOWNLOAD_TIMEOUT)
    except requests.exceptions.RequestException as e:
        error = f"request_get(): there was a problem downloading {url}."
        if not ignore_errors:
            raise HttpError(error) from e
        print(error)
        return b""

    if check_for_bad_response(url, gotten, **kwargs):
        # Note: check_for_bad_response() will raise an exception
        # if it encounters a problem and ignore_errors is False.
        # Otherwise it will print an error message and return True
        return b""

    return gotten.content  # bytes


def save_to_cache(
    file: Path,
    contents: bytes,
    **kwargs: Unpack[FileKwargs],
) -> None:
    """Save bytes to the file-system cache using atomic replacement.

    Uses atomic file replacement to ensure cache integrity. The file is written
    to a temporary location first, then atomically moved to the final location.
    This prevents corruption from interrupted writes and race conditions.

    Args:
        file: Path object for the cache file location
        contents: Bytes content to save
        **kwargs: Optional parameters including 'verbose' (bool)

    Raises:
        OSError: If file operations fail (disk full, permissions, etc.)

    """
    verbose = kwargs.get("verbose", False)
    if len(contents) == 0:
        # don't save empty files (probably caused by ignoring errors)
        return

    if verbose:
        print(f"About to save to cache: {file}")

    # Create temporary file with .tmp suffix in same directory
    temp_file = file.with_suffix(file.suffix + ".tmp")

    try:
        # Write content to temporary file first
        temp_file.write_bytes(contents)

        # Atomic move - this is the critical operation
        # On Unix/Linux, this is a single syscall and truly atomic
        temp_file.replace(file)

        if verbose:
            print(f"Successfully saved to cache: {file}")

    except OSError:
        # Clean up temp file if something went wrong
        if temp_file.exists():
            temp_file.unlink()
        raise


def retrieve_from_cache(file: Path, **kwargs: Unpack[FileKwargs]) -> bytes:
    """Retrieve bytes from file-system cache.

    Args:
        file: Path object for the cache file location
        **kwargs: Optional parameters including 'verbose' and 'ignore_errors'

    Returns:
        bytes: The cached content, or empty bytes if error ignored

    Raises:
        CacheError: If file doesn't exist and ignore_errors is False

    """
    verbose = kwargs.get("verbose", False)
    ignore_errors = kwargs.get("ignore_errors", False)

    if not file.exists() or not file.is_file():
        message = f"Cached file not available: {file.name}"
        if ignore_errors:
            print(message)
            return b""
        raise CacheError(message)
    if verbose:
        print(f"Retrieving from cache: {file}")
    return file.read_bytes()


def _download_if_fresh(
    url: str,
    file_path: Path,
    **kwargs: Unpack[FileKwargs],
) -> bytes | None:
    """Download from the URL if it is fresher than the cached copy.

    Compares the URL's HTTP Last-Modified header against the cache file's
    modification time. Downloads, caches and returns the fresh content when the
    URL is newer (or nothing is cached yet). Returns None when the cached copy
    is already up to date and should be used instead.

    Args:
        url: The URL to download from
        file_path: Path object for the cache file location
        **kwargs: Optional parameters including 'verbose' and 'ignore_errors'

    Returns:
        bytes | None: Fresh content if downloaded, or None if the cache is current

    Raises:
        HttpError: If the download fails (or returns no data)
        requests.exceptions.RequestException: If the network is unreachable

    """
    verbose = kwargs.get("verbose", False)

    # get URL modification time in UTC (raises if the network is unreachable)
    response = requests.head(url, allow_redirects=True, timeout=HEAD_REQUEST_TIMEOUT)
    if not check_for_bad_response(url, response, **kwargs):
        source_time = response.headers.get("Last-Modified", None)
    else:
        source_time = None
    source_mtime = None if source_time is None else pd.to_datetime(source_time, utc=True)

    # get cache modification time in UTC
    target_mtime: datetime | None = None
    if file_path.exists() and file_path.is_file():
        target_mtime = pd.to_datetime(
            datetime.fromtimestamp(file_path.stat().st_mtime, tz=UTC),
            utc=True,
        )

    # the cache is present and not superseded by the URL - use the cache
    if target_mtime is not None and (source_mtime is None or source_mtime <= target_mtime):
        return None

    # the cache is empty or stale - download and save the fresh content
    if verbose:
        print(f"Retrieving from URL: {url}")
    url_bytes = request_get(url, **kwargs)  # raises exception if it fails
    if len(url_bytes) == 0:
        # treat an empty download as a failure so the caller can fall back to cache
        raise HttpError(f"No data downloaded from {url}.")
    if verbose:
        print(f"Saving to cache: {file_path}")
    save_to_cache(file_path, url_bytes, **kwargs)
    # change file mod time to reflect mtime at URL
    if source_mtime is not None:
        unixtime = source_mtime.value / NANOSECONDS_PER_SECOND
        utime(file_path, (unixtime, unixtime))
    return url_bytes


def _stale_cache_fallback(
    file_path: Path,
    url: str,
    error: Exception,
    **kwargs: Unpack[FileKwargs],
) -> bytes:
    """Fall back to the cached copy when fresh data could not be downloaded.

    Returns the cached bytes (with a prominent warning that the data may be
    stale) when a cached copy exists. Otherwise honours 'ignore_errors' or
    raises. This is what lets readabs keep working offline (e.g. on a plane).

    Args:
        file_path: Path object for the cache file location
        url: The URL that could not be downloaded
        error: The exception that prevented a fresh download
        **kwargs: Optional parameters including 'ignore_errors'

    Returns:
        bytes: The cached content, or empty bytes if errors are ignored

    Raises:
        HttpError: If no cached copy exists and ignore_errors is False

    """
    if file_path.exists() and file_path.is_file():
        cached_mtime = datetime.fromtimestamp(file_path.stat().st_mtime, tz=UTC)
        # always warn (regardless of verbose) - the user needs to know it is stale
        print(
            f"WARNING: could not download fresh data for {url}.\n"
            f"  Reason: {error}\n"
            f"  Falling back to cached data last modified "
            f"{cached_mtime:%Y-%m-%d %H:%M UTC} - this data may be out of date.",
        )
        return file_path.read_bytes()

    message = f"Could not download {url} ({error}), and no cached copy is available."
    if kwargs.get("ignore_errors", False):
        print(message)
        return b""
    raise HttpError(message)


def get_file(
    url: str,
    cache_dir: Path = READABS_CACHE_PATH,
    cache_prefix: str = "cache",
    **kwargs: Unpack[FileKwargs],
) -> bytes:
    """Get a file from URL or local file-system cache, depending on freshness.

    Downloads from URL if cached version doesn't exist or is stale based on
    HTTP Last-Modified headers. Creates cache_dir if it doesn't exist.

    If fresh data cannot be downloaded (for example, the internet is
    unreachable), and a cached copy exists, the cached copy is returned with a
    warning that the data may be out of date. An error is only raised when there
    is no cached copy to fall back to (and 'ignore_errors' is not set).

    Args:
        url: The URL to download from
        cache_dir: Directory path for cache storage
        cache_prefix: Prefix for cache filenames
        **kwargs: Optional parameters including 'verbose', 'ignore_errors', 'cache_only'

    Returns:
        bytes: The file contents

    Raises:
        CacheError: If cache directory cannot be created or accessed
        HttpError: If download fails, ignore_errors is False, and no cache exists

    """

    def get_fpath() -> Path:
        """Convert URL string into a cache file name and return as Path object."""
        hash_name = sha256(url.encode("utf-8")).hexdigest()
        tail_name = url.rsplit("/", 1)[-1].split("?", 1)[0]
        file_name = re.sub(BAD_CACHE_PATTERN, "", f"{cache_prefix}--{hash_name}--{tail_name}")
        return Path(cache_dir / file_name)

    # create and check cache_dir is a directory
    cache_dir.mkdir(parents=True, exist_ok=True)
    if not cache_dir.is_dir():
        raise CacheError(f"Cache path is not a directory: {cache_dir.name}")

    file_path = get_fpath()  # the cache file path

    # cache-only mode never touches the network
    if kwargs.get("cache_only", False):
        return retrieve_from_cache(file_path, **kwargs)

    # attempt to download fresh data, falling back to a stale cache on failure
    try:
        fresh = _download_if_fresh(url, file_path, **kwargs)
    except (HttpError, requests.exceptions.RequestException) as e:
        return _stale_cache_fallback(file_path, url, e, **kwargs)

    if fresh is not None:
        return fresh

    # the cache is already up to date - return it
    return retrieve_from_cache(file_path, **kwargs)


# --- preliminary testing:
if __name__ == "__main__":

    def cache_test() -> None:
        """Test the retrieval and caching system.

        Downloads a file twice to demonstrate caching behavior.
        Clear the cache directory first to see the full effect.
        """
        # prepare the test case
        url1 = (
            "https://www.abs.gov.au/statistics/labour/employment-and-"
            "unemployment/labour-force-australia/nov-2023/6202001.xlsx"
        )

        # implement - first retrieval is from the web, second from the cache
        width = 20
        print("Test commencing.")
        for u in (url1, url1):
            print("=" * width)
            content = get_file(u, verbose=True)
            print("-" * width)
            print(f"{len(content)} bytes retrieved from {u}.")
        print("=" * width)
        print("Test completed.")

    cache_test()
