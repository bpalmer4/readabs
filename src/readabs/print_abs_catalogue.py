"""Print the ABS Catalogue of time-series data."""

from readabs.abs_catalogue import CatalogueError, abs_catalogue
from readabs.download_cache import CacheError, HttpError

# Constants for display formatting
DISPLAY_COLUMNS = ["Theme", "Parent Topic", "Topic", "Status"]


def print_abs_catalogue(*, cache_only: bool = False, verbose: bool = False) -> None:
    """Print a table of ABS Catalogue Numbers with their metadata.

    Displays catalogue numbers that contain time-series data along with
    their theme, parent topic, topic, and status information. The URL
    column is excluded from the display for readability.

    This is primarily a convenience function to help users identify the
    correct catalogue number for data retrieval functions.

    Parameters
    ----------
    cache_only : bool, default False
        If True, only use cached catalogue data.
    verbose : bool, default False
        If True, print progress messages during catalogue retrieval.

    Raises
    ------
    CatalogueError
        If the catalogue data cannot be retrieved or processed.
    HttpError
        If there's a network error downloading the catalogue.
    CacheError
        If cache_only=True but no cached data is available.

    Example
    -------
    >>> import readabs as ra
    >>> ra.print_abs_catalogue()

    """
    try:
        # Retrieve the catalogue data
        catalogue = abs_catalogue(cache_only=cache_only, verbose=verbose)

        # Validate catalogue is not empty
        if catalogue.empty:
            print("No catalogue data available.")
            return

        # Select columns for display (exclude URL for readability)
        available_columns = [col for col in DISPLAY_COLUMNS if col in catalogue.columns]
        if not available_columns:
            print("Catalogue data does not contain expected columns.")
            return

        display_data = catalogue[available_columns]

        # Generate and print markdown table
        try:
            markdown_output = display_data.to_markdown()
            print(markdown_output)
        except Exception:  # noqa: BLE001
            print(display_data.to_string())

    except (CatalogueError, HttpError, CacheError) as e:
        print(f"Error retrieving catalogue: {e}")


if __name__ == "__main__":
    print_abs_catalogue()
