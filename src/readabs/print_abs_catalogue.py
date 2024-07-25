"""Print the ABS Catalogue of time-series data."""

from readabs.abs_catalogue import abs_catalogue


def print_abs_catalogue(cache_only=False, verbose=False) -> None:
    """This function prints to standard output a table of the ABS
    Catalogue Numbers that contain time-series data. In addition to the
    Catalogue Numbers, the table includes the theme, parent topic and
    topic for the collection represented by each Catalogue Number.

    It is primarily a convenience function: The first parameter for
    the read_abs_cat() and read_abs_series() functions is the ABS
    Catalogue Number from which data is sought.

    Parameters
    ----------
    cache_only : bool = False
        If True, only use the cache.
    verbose : bool = False
        If True, print progress messages.

    Return values
    -------------

    The function does not return anything.

    Example
    -------

    ```python
    import readabs as ra
    ra.print_abs_catalogue()
    ```"""

    catalogue = abs_catalogue(cache_only=cache_only, verbose=verbose)
    print(catalogue.loc[:, catalogue.columns != "URL"].to_markdown())


if __name__ == "__main__":
    print_abs_catalogue()
