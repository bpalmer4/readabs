"""Catalogue map for ABS data."""

from functools import cache
from io import StringIO

from pandas import DataFrame, Index, Series, read_html

from readabs.download_cache import CacheError, HttpError, get_file

# Constants
ABS_CATALOGUE_URL = "https://www.abs.gov.au/about/data-services/help/abs-time-series-directory"
ABS_STATISTICS_ROOT = "https://www.abs.gov.au/statistics/"
EXPECTED_COLUMNS = ["Theme", "Parent Topic", "Topic"]
CATALOGUE_INDEX_NAME = "Catalogue ID"
CEASED_MARKER = "Ceased"
DEFAULT_ENCODING = "utf-8"


class CatalogueError(Exception):
    """Error processing ABS catalogue data."""


@cache
def abs_catalogue(*, cache_only: bool = False, verbose: bool = False) -> DataFrame:
    """Return a DataFrame of ABS Catalogue numbers.

    Downloads catalogue data from the ABS website on first call and caches
    for future use. The returned DataFrame contains catalogue numbers with
    their topics, themes, URLs, and status.

    Parameters
    ----------
    cache_only : bool, default False
        If True, only use cached data and don't attempt to download.
    verbose : bool, default False
        If True, print progress messages.

    Returns
    -------
    DataFrame
        DataFrame with columns ['Theme', 'Parent Topic', 'Topic', 'URL', 'Status']
        and index of catalogue IDs.

    Raises
    ------
    CatalogueError
        If the catalogue data cannot be retrieved or parsed.
    HttpError
        If there's a network error downloading the catalogue.
    CacheError
        If cache_only=True but no cached data is available.

    Example
    -------
    >>> import readabs as ra
    >>> catalogue = ra.abs_catalogue()
    >>> print(catalogue.head())

    """
    try:
        # Download ABS catalogue page
        abs_bytes = get_file(ABS_CATALOGUE_URL, cache_only=cache_only, verbose=verbose)

        if not abs_bytes:
            raise CatalogueError("No data retrieved from ABS catalogue URL")

        # Parse HTML content
        try:
            html_content = abs_bytes.decode(DEFAULT_ENCODING, errors="replace")
        except UnicodeDecodeError as e:
            raise CatalogueError(f"Failed to decode HTML content: {e}") from e

        # Extract tables from HTML
        try:
            tables = read_html(StringIO(html_content), extract_links="body")
            if not tables:
                raise CatalogueError("No tables found in HTML content")
            links = tables[-1]  # Get the last table
        except (ValueError, IndexError) as e:
            raise CatalogueError(f"Failed to parse HTML tables: {e}") from e

        # Validate required columns exist
        required_cols = ["Catalogue number", "Topic"]
        missing_cols = [col for col in required_cols if col not in links.columns]
        if missing_cols:
            raise CatalogueError(f"Missing required columns: {missing_cols}")

        # Extract catalogue numbers and URLs
        try:
            cats = links["Catalogue number"].apply(Series)[0]
            urls = links["Topic"].apply(Series)[1]
        except (KeyError, IndexError) as e:
            raise CatalogueError(f"Failed to extract catalogue data: {e}") from e

        # Process topic URLs to create hierarchical structure
        url_snippets = _process_topic_urls(urls)

        # Create main DataFrame with hierarchical topic structure
        frame = _create_topic_frame(url_snippets)
        frame["URL"] = urls

        # Align catalogue numbers with processed frame
        cats = cats[frame.index]

        # Process catalogue status (active vs ceased)
        cat_index, status = _process_catalogue_status(cats)

        frame["Status"] = status
        frame.index = Index(cat_index)
        frame.index.name = CATALOGUE_INDEX_NAME

    except (HttpError, CacheError, ValueError) as e:
        raise CatalogueError(f"Error retrieving ABS catalogue: {e}") from e

    return frame


def _process_topic_urls(urls: Series) -> Series:
    """Process topic URLs to extract clean topic hierarchy."""
    # Remove root URL prefix
    snippets = urls.str.replace(ABS_STATISTICS_ROOT, "", regex=False)

    # Filter out invalid URLs and clean formatting
    valid_snippets = snippets[~snippets.str.contains("http", na=False)]
    return valid_snippets.str.replace("-", " ").str.title()


def _create_topic_frame(snippets: Series) -> DataFrame:
    """Create DataFrame with topic hierarchy from URL snippets."""
    # Split URL paths into hierarchical components
    frame = snippets.str.split("/", expand=True).iloc[:, :3]
    frame.columns = Index(EXPECTED_COLUMNS)

    return frame


def _process_catalogue_status(cats: Series) -> tuple[Series, Series]:
    """Process catalogue numbers to extract IDs and status."""
    # Extract clean catalogue IDs (remove ceased marker)
    cat_index = cats.str.replace(CEASED_MARKER, "", regex=False).str.strip()

    # Determine status based on presence of ceased marker
    status = Series("Active", index=cats.index)
    ceased_mask = cats.str.contains(CEASED_MARKER, na=False)
    status.loc[ceased_mask] = "Ceased"

    return cat_index, status


if __name__ == "__main__":
    print(abs_catalogue())
