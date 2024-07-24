"""print_abs_catalogue.py

Print the ABS Catalogue of time-series data."""

from readabs.abs_catalogue_map import abs_catalogue


def print_abs_catalogue() -> None:
    """Print the ABS catalogue."""
    catalogue = abs_catalogue()
    print(catalogue.loc[:, catalogue.columns != "URL"].to_markdown())


if __name__ == "__main__":
    # type: ignore
    print_abs_catalogue()
