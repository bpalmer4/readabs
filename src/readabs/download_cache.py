"""download_cache.py - a module for downloading and caching data from the web.

The default cache directory can be specified by setting the environment 
variable READABS_CACHE_DIR."""

# --- imports
# system imports
from hashlib import md5
import re
from datetime import datetime, timezone
from os import utime, getenv
from pathlib import Path
from typing import Any

# data imports
import pandas as pd
import requests


# --- constants
# define the default cache directory
DEFAULT_CACHE_DIR = "./.readabs_cache"
READABS_CACHE_DIR = getenv("READABS_CACHE_DIR", DEFAULT_CACHE_DIR)
READABS_CACHE_PATH = Path(READABS_CACHE_DIR)

DOWNLOAD_TIMEOUT = 60  # seconds


# --- Exception classes
class HttpError(Exception):
    """A problem retrieving data from HTTP."""


class CacheError(Exception):
    """A problem retrieving data from the cache."""


# --- functions
def check_for_bad_response(
    url: str,
    response: requests.Response,
    **kwargs: Any,
) -> bool:
    """Raise an Exception if we could not retrieve the URL.
    If "ignore_errors" is True, return True if there is a problem,
    otherwise raise an exception if there is a problem."""

    ignore_errors = kwargs.get("ignore_errors", False)
    code = response.status_code
    if code != 200 or response.headers is None:
        problem = f"Problem {code} accessing: {url}."
        if not ignore_errors:
            raise HttpError(problem)
        print(problem)
        return True

    return False


def request_get(
    url: str,
    **kwargs: Any,
) -> bytes:
    """Use python requests to get the contents of the specified URL.
    Depending on "ignore_errors", if something goes wrong, we either
    raise an exception or return an empty bytes object."""

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
    **kwargs: Any,
) -> None:
    """Save bytes to the file-system."""

    verbose = kwargs.get("verbose", False)
    if len(contents) == 0:
        # dont save empty files (probably caused by ignoring errors)
        return
    if file.exists():
        if verbose:
            print("Removing old cache file.")
        file.unlink()
    if verbose:
        print(f"About to save to cache: {file}")
    file.open(mode="w", buffering=-1, encoding=None, errors=None, newline=None)
    file.write_bytes(contents)


def retrieve_from_cache(file: Path, **kwargs: Any) -> bytes:
    """Retrieve bytes from file-system."""

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


def get_file(
    url: str,
    cache_dir: Path = READABS_CACHE_PATH,
    cache_prefix: str = "cache",
    **kwargs: Any,
) -> bytes:
    """Get a file from URL or local file-system cache, depending on freshness.
    Note: we create the cache_dir if it does not exist.
    Returns: the contents of the file as bytes."""

    def get_fpath() -> Path:
        """Convert URL string into a cache file name,
        then return as a Path object."""
        bad_cache_pattern = r'[~"#%&*:<>?\\{|}]+'  # chars to remove from name
        hash_name = md5(url.encode("utf-8")).hexdigest()
        tail_name = url.split("/")[-1].split("?")[0]
        file_name = re.sub(
            bad_cache_pattern, "", f"{cache_prefix}--{hash_name}--{tail_name}"
        )
        return Path(cache_dir / file_name)

    # create and check cache_dir is a directory
    cache_dir.mkdir(parents=True, exist_ok=True)
    if not cache_dir.is_dir():
        raise CacheError(f"Cache path is not a directory: {cache_dir.name}")

    # get URL modification time in UTC
    file_path = get_fpath()  # the cache file path
    if not kwargs.get("cache_only", False):
        # download from url if it is fresher than the cache version
        response = requests.head(url, allow_redirects=True, timeout=20)
        if not check_for_bad_response(url, response, **kwargs):
            source_time = response.headers.get("Last-Modified", None)
        else:
            source_time = None
        source_mtime = (
            None if source_time is None else pd.to_datetime(source_time, utc=True)
        )

        # get cache modification time in UTC
        target_mtime: datetime | None = None
        if file_path.exists() and file_path.is_file():
            target_mtime = pd.to_datetime(
                datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc),
                utc=True,
            )

        # get and save URL source data
        if target_mtime is None or (  # cache is empty, or
            source_mtime is not None
            and source_mtime > target_mtime  # URL is fresher than cache
        ):
            url_bytes = request_get(url, **kwargs)  # raises exception if it fails
            save_to_cache(file_path, url_bytes, **kwargs)
            # - change file mod time to reflect mtime at URL
            if source_mtime is not None and len(url_bytes) > 0:
                unixtime = source_mtime.value / 1_000_000_000  # convert to seconds
                utime(file_path, (unixtime, unixtime))
            return url_bytes

    # return the data that has been cached previously
    return retrieve_from_cache(file_path, **kwargs)


# --- preliminary testing:
DO_TEST = False
if __name__ == "__main__" and DO_TEST:

    def cache_test() -> None:
        """This function provides a quick test of the retrieval
        and caching system.  You may need to first clear the
        cache directory to see the effect of the cache."""

        # prepare the test case
        url1 = (
            "https://www.abs.gov.au/statistics/labour/employment-and-"
            + "unemployment/labour-force-australia/nov-2023/6202001.xlsx"
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
