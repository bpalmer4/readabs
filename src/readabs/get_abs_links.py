"""Scan an ABS webpage for links to Excel and zip files."""

from pathlib import Path
from typing import NotRequired, Unpack
from urllib.parse import urlparse

from bs4 import BeautifulSoup, Tag

# local imports
from readabs.download_cache import CacheError, FileKwargs, HttpError, get_file

# --- Constants
DEFAULT_ABS_PREFIX = "https://www.abs.gov.au"
SUPPORTED_FILE_TYPES = (".zip", ".xlsx")  # must be lowercase
DEFAULT_ENCODING = "utf-8"


class LinksKwargs(FileKwargs):
    """Additional keyword arguments for get_abs_links().

    This class extends FileKwargs to include options specific to ABS link retrieval.
    """

    history: NotRequired[str]


# --- private
def _make_absolute_url(link_url: str, prefix: str = DEFAULT_ABS_PREFIX) -> str:
    """Convert a relative URL to an absolute URL.

    Args:
        link_url: The URL to convert (relative or absolute)
        prefix: The base URL prefix to use for relative URLs

    Returns:
        str: The absolute URL

    """
    # If already absolute, return as-is
    if urlparse(link_url).netloc:
        return link_url

    # Remove any existing prefix to handle edge cases
    clean_url = link_url.replace(prefix, "")
    clean_url = clean_url.replace(prefix.replace("https://", "http://"), "")

    # Ensure URL starts with / for proper joining
    if not clean_url.startswith("/"):
        clean_url = "/" + clean_url

    return f"{prefix}{clean_url}"


# --- private
def historicise_links(link_dict: dict[str, list[str]], history: str) -> dict[str, list[str]]:
    """Convert ABS links to point to historical versions of the data.

    Modifies URLs by inserting the history string in the expected location.
    The history string is typically in "mon-yr" format (e.g., "dec-2022").
    Assumes the date should be inserted as the second-to-last path component.

    Args:
        link_dict: Dictionary mapping file types to lists of URLs
        history: History string to insert into URLs (e.g., "dec-2022")

    Returns:
        dict[str, list[str]]: New dictionary with historicized URLs

    Note:
        This function makes assumptions about ABS URL structure that may not
        always hold. Use with caution.

    """
    new_dict = {}
    for link_type, link_list in link_dict.items():
        new_list = []
        for link in link_list:
            head, _, tail = link.rsplit("/", 2)
            replacement = f"{head}/{history}/{tail}"
            new_list.append(replacement)
        new_dict[link_type] = new_list

    return new_dict


# --- public (also used by grab_abs_url.py)
def get_table_name(url: str) -> str:
    """Extract the table name from an ABS URL.

    Args:
        url: The ABS URL containing a table file

    Returns:
        str: The table name (filename without extension)

    """
    tail = url.rsplit("/", 1)[-1]
    return tail.split(".")[0]


def _download_page(url: str, **kwargs: Unpack[LinksKwargs]) -> bytes | None:
    """Download webpage content from URL."""
    try:
        return get_file(
            url,
            verbose=kwargs.get("verbose", False),
            ignore_errors=kwargs.get("ignore_errors", False),
            cache_only=kwargs.get("cache_only", False),
        )
    except (HttpError, CacheError) as e:
        print(f"Error when obtaining links from ABS web page: {e}")
        return None


def _parse_html(page: bytes, *, verbose: bool = False) -> BeautifulSoup | None:
    """Parse HTML content and return BeautifulSoup object."""
    try:
        return BeautifulSoup(page, features="lxml")
    except Exception as e:  # noqa: BLE001
        if verbose:
            print(f"Error parsing HTML: {e}")
        return None


def _extract_file_links(soup: BeautifulSoup) -> dict[str, list[str]]:
    """Extract download links from parsed HTML."""
    link_dict: dict[str, list[str]] = {}

    for element in soup.find_all("a"):
        if not isinstance(element, Tag):
            continue
        link_href = element.get("href")
        if not link_href or not isinstance(link_href, str) or "Mock-up" in link_href:
            continue

        for file_type in SUPPORTED_FILE_TYPES:
            if link_href.lower().endswith(file_type):
                if file_type not in link_dict:
                    link_dict[file_type] = []
                link_dict[file_type].append(_make_absolute_url(link_href))
                break

    return link_dict


def _print_summary(link_dict: dict[str, list[str]]) -> None:
    """Print summary of found links."""
    print("Found links to the following ABS data tables:")
    for link_type, link_list in link_dict.items():
        summary = [get_table_name(x) for x in link_list]
        print(f"Found: {len(link_list)} items of type {link_type}: {summary}")
    print()


# --- public
def get_abs_links(
    url: str = "",
    inspect_file_name: str = "",
    **kwargs: Unpack[LinksKwargs],
) -> dict[str, list[str]]:
    """Scan an ABS webpage for downloadable file links.

    Args:
        url: The ABS webpage URL to scan
        inspect_file_name: Optional filename to save webpage for debugging
        **kwargs: Additional options (verbose, history, cache_only, ignore_errors)

    Returns:
        dict[str, list[str]]: Dictionary mapping file extensions to lists of URLs

    """
    verbose = kwargs.get("verbose", False)

    if not url:
        if verbose:
            print("No URL provided to get_abs_links()")
        return {}

    # Download webpage
    page = _download_page(url, **kwargs)
    if not page:
        return {}

    # Save for debugging if requested
    _debug_later(inspect_file_name, page=page)

    # Parse HTML
    soup = _parse_html(page, verbose=verbose)
    if not soup:
        return {}

    # Extract links
    link_dict = _extract_file_links(soup)

    # Apply historical versioning if requested
    history = kwargs.get("history", "")
    if history:
        link_dict = historicise_links(link_dict, history)

    # Print summary if verbose
    if verbose:
        _print_summary(link_dict)

    return link_dict


# --- private
def _debug_later(inspect_file_name: str, page: bytes) -> None:
    """Save webpage content to file for debugging purposes.

    Args:
        inspect_file_name: Path where to save the file (if provided)
        page: The webpage content as bytes

    """
    if inspect_file_name:
        try:
            debug_path = Path(inspect_file_name)
            with debug_path.open("w", encoding=DEFAULT_ENCODING) as file_handle:
                file_handle.write(page.decode(DEFAULT_ENCODING, errors="replace"))
        except (OSError, UnicodeDecodeError) as e:
            print(f"Warning: Could not save debug file {inspect_file_name}: {e}")


# --- testing
if __name__ == "__main__":

    def test_get_abs_links() -> None:
        """Test the get_abs_links() function with a sample ABS URL."""
        url = (
            "https://www.abs.gov.au/statistics/people/population/"
            "national-state-and-territory-population/latest-release"
        )

        _links = get_abs_links(url, history="dec-2022", verbose=True)

    test_get_abs_links()
