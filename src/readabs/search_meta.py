"""search_meta.py

Search a DataFrame of ABS meta data, using a dictionary of search terms,
to identify the row or rows that match all of the search terms."""

from typing import Any
from pandas import DataFrame

# local imports - ugly, need to find out how to fix thiscd
if __package__ is None or __package__ == "":
    from abs_meta_data_support import metacol
else:
    from .abs_meta_data_support import metacol


def search_meta(
    meta: DataFrame,  # sourced from read_abs_series() or read_abs_cat()
    search_terms: dict[str, str],  # {search_term: meta_data_column_name, ...}
    exact_match: bool = False,
    regex: bool = False,
    validate_unique=False,  # useful safety-net if you expect only one match
    **kwargs: Any,
) -> DataFrame:
    """Extract from the meta data the rows that match the search_terms, by iteratively
    searching the meta data one search term at a time.

    Arguments:
     - meta - pandas DataFrame of metadata from the ABS
       (via read_abs_cat() or read_abs_series()).
     - search_terms - dictionary - {search_phrase: meta_column_name, ...}
       Note: the search terms must be unique, as a dictionary cannot hold the
       same search term to be applied to different columns.
     - exact_natch - bool - whether to match using == (exact) or .str.contains()
       (inexact)
     - regex - bool - for .str.contains() - whether to use regular expressions
     - validate_unique - bool - raise a ValueError if search result is not unique
     - verbose - bool - print additional information while searching; which can
       be useful when diagnosing problems with search terms.

    Returns a pandas DataFrame (subseted from meta), Note: The index for the
    returned meta data will always comprise ABS series_ids. Duplicate indexes
    will be removed from the meta data (ie. where the ABS has a series in more
    than one table, this function will only report the first match.)"""

    # get the verbose-flag from kwargs
    verbose = kwargs.get("verbose", False)

    # establish the starting point
    meta_select = meta.copy()  # preserve the original meta data
    if verbose:
        print(f"In search_meta() {exact_match=} {regex=} {verbose=}")
        print(
            f"In search_meta() starting with {len(meta_select)} rows in the meta_data."
        )

    # iteratively search
    for phrase, column in search_terms.items():
        if verbose:
            print(f"Searching {len(meta_select)}: term: {phrase} in-column: {column}")

        pick_me = (
            (meta_select[column] == phrase)
            if (exact_match or column == metacol.table)
            else meta_select[column].str.contains(phrase, regex=regex)
        )
        meta_select = meta_select[pick_me]
        if verbose:
            print(f"In find_rows() have found {len(meta_select)}")

    # search complete - check results - and return
    meta_select.index = meta_select[metacol.id]
    meta_select = meta_select[~meta_select.index.duplicated(keep="first")]

    if verbose:
        print(f"Final selection is {len(meta_select)} rows.")

    elif len(meta_select) == 0:
        print("Nothing selected?")

    if validate_unique and len(meta_select) != 1:
        raise ValueError("The selected meta data should only contain one row.")

    return meta_select


def find_id(
    meta: DataFrame,
    search_terms: dict[str, str],
    **kwargs: Any,
) -> tuple[str, str, str]:  # table, series_id, units
    """Find a unique ABS series id in the meta data.
    Return a tuple of the table, series_id and units.
    By default, raises a ValueError if the search terms do
    not result in one and only one series_id.
    Arguments are the same as for search_meta()."""

    validate_unique = kwargs.pop("validate_unique", True)
    found = search_meta(
        meta, search_terms, validate_unique=validate_unique, **kwargs
    ).iloc[0]
    table, series_id, units = (
        found[metacol.table],
        found[metacol.id],
        found[metacol.unit],
    )

    return table, series_id, units
