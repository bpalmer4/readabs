"""Search a DataFrame of ABS meta data, using a dictionary of search terms,
to identify the row or rows that match all of the search terms."""

from typing import Any
from pandas import DataFrame, Index

# local imports
from readabs.abs_meta_data import metacol as mc
from readabs.read_abs_cat import read_abs_cat


def search_abs_meta(
    meta: DataFrame,  # sourced from read_abs_series() or read_abs_cat()
    search_terms: dict[str, str],  # {search_term: meta_data_column_name, ...}
    exact_match: bool = False,
    regex: bool = False,
    validate_unique=False,  # useful safety-net if you expect only one match
    **kwargs: Any,
) -> DataFrame:
    """Extract from the ABS meta data those rows that match the
    search_terms, by iteratively searching the meta data one
    search_term at a time.

    Parameters
    ----------
    meta : DataFrame
        A pandas DataFrame of metadata from the ABS
        (via read_abs_cat() or read_abs_series()).
    search_terms : dict[str, str]
        A dictionary {search_phrase: meta_column_name, ...} of search terms.
        Note: the search terms must be unique, as a dictionary cannot hold the
        same search term to be applied to different columns.
    exact_match : bool = False
        Whether to match using == (exact) or .str.contains() (inexact).
    regex : bool = False
        Whether to use regular expressions in the search.
    validate_unique : bool = False
        Raise a ValueError if the search result is not unique.
    **kwargs : Any
        Additional keyword arguments. The only keyword argument
        that is used is verbose.
    verbose : bool = False
        Print additional information while searching; which can
        be useful when diagnosing problems with search terms.

    Returns
    -------
    DataFrame
        Returns a pandas DataFrame of matching rows (subseted from meta).
        Note, The index for the returned meta data will always comprise ABS
        series_ids. Duplicate indexes will be removed from the meta data
        (ie. where the same ABS series appears in more than one table, this
        function will only report the first match).

    Metacol
    -------
    Because the meta data is a DataFrame, the columns can be referenced by either
    their full textual name, or by the short name defined in the metacol object.
    For example, if metacol is imported as mc, to refer to the
    `Data Item Description` column, the user can refer to it as mc.did.

    Example
    -------
    ```python
    from readabs import metacol as mc  # alias for the ABS meta data column names
    from readabs import read_abs_cat, search_abs_meta
    cat_num = "6202.0"  # The ABS labour force survey
    data, meta = read_abs_cat(cat_num)
    search_terms = {
        "Unemployment rate": mc.did,  # the data item description
        "Persons": mc.did,
        "Seasonally Adjusted": mc.stype,
        "Percent": mc.unit,
        "6202001": mc.table,
    }
    rows = search_abs_meta(meta, search_terms, verbose=True)
    print(rows)  # should have three rows : FT/PT/All Unemployment rates
    ```"""

    # get the verbose-flag from kwargs
    verbose = kwargs.get("verbose", False)

    # establish the starting point
    meta_select = meta.copy()  # preserve the original meta data
    if verbose:
        print(f"In search_abs_meta() {exact_match=} {regex=} {verbose=}")
        print(
            f"In search_abs_meta() starting with {len(meta_select)} rows in the meta_data."
        )

    # iteratively search
    for phrase, column in search_terms.items():
        if verbose:
            print(f"Searching {len(meta_select)}: term: {phrase} in-column: {column}")

        pick_me = (
            (meta_select[column] == phrase)
            if (exact_match or column == mc.table)
            else meta_select[column].str.contains(phrase, regex=regex)
        )
        meta_select = meta_select[pick_me]
        if verbose:
            print(f"In find_rows() have found {len(meta_select)}")

    # search complete - check results - and return
    meta_select.index = Index(meta_select[mc.id])
    meta_select = meta_select[~meta_select.index.duplicated(keep="first")]

    if verbose:
        print(f"Final selection is {len(meta_select)} rows.")

    elif len(meta_select) == 0:
        print("Nothing selected?")

    if validate_unique and len(meta_select) != 1:
        raise ValueError("The selected meta data should only contain one row.")

    return meta_select


def find_abs_id(
    meta: DataFrame,
    search_terms: dict[str, str],
    **kwargs: Any,
) -> tuple[str, str, str]:  # table, series_id, units
    """Find a unique ABS series identifier in the ABS metadata.

    Parameters
    ----------
    meta : DataFrame
        A pandas DataFrame of metadata from the ABS
        (via read_abs_cat() or read_abs_series()).
    search_terms : dict[str, str]
        A dictionary {search_phrase: meta_column_name, ...} of search terms.
        Note: the search terms must be unique, as a dictionary cannot hold the
        same search term to be applied to different columns.
    **kwargs : Any
        Additional keyword arguments. The only additional keyword argument
        that is used is validate_unique.
    validate_unique : bool = True
        Raise a ValueError if the search result is not a single
        unique match. Note: the default is True for safety.

    Returns
    -------
    tuple[str, str, str]
        A tuple of the table, series_id and units for the unique
        series_id that matches the search terms.

    Metacol
    -------
    Because the meta data is a DataFrame, the columns can be referenced by either
    their full textual name, or by the short name defined in the metacol object.
    For example, if metacol is imported as mc, to refer to the
    `Data Item Description` column, the user can refer to it as mc.did.

    Example
    -------
    ```python
    from readabs import metacol as mc  # alias for the ABS meta data column names
    from readabs import read_abs_cat, find_abs_id, recalibrate
    cat_num = "6202.0"  # The ABS labour force survey
    data, meta = read_abs_cat(cat_num)
    search_terms = {
        "Employed total ;  Persons ;": mc.did,
        "Seasonally Adjusted": mc.stype,
        "6202001": mc.table,
    }
    table, series_id, units = find_abs_id(meta, search_terms)
    print(f"Table: {table} Series ID: {series_id} Units: {units}")
    recal_series, recal_units = recalibrate(data[table][series_id], units)
    ```"""

    validate_unique = kwargs.pop("validate_unique", True)
    found = search_abs_meta(
        meta, search_terms, validate_unique=validate_unique, **kwargs
    ).iloc[0]
    table, series_id, units = (
        found[mc.table],
        found[mc.id],
        found[mc.unit],
    )

    return table, series_id, units


if __name__ == "__main__":

    def test_search_abs_meta():
        """Test the search_abs_meta() function."""

        cat_num = "6202.0"  # The ABS labour force survey
        _data, meta = read_abs_cat(cat_num)
        search_terms = {
            "Unemployment rate": mc.did,  # the data item description
            "Persons": mc.did,
            "Seasonally Adjusted": mc.stype,
            "Percent": mc.unit,
            "6202001": mc.table,
        }
        rows = search_abs_meta(meta, search_terms, verbose=True)
        print(rows)  # should have three rows : FT/PT/All Unemplooyment rates

    test_search_abs_meta()

    def test_find_abs_id():
        """Test the find_abs_id() function."""

        cat_num = "6202.0"  # The ABS labour force survey
        _data, meta = read_abs_cat(cat_num)
        search_terms = {
            "Employed total ;  Persons ;": mc.did,
            "Seasonally Adjusted": mc.stype,
            "6202001": mc.table,
        }
        table, series_id, units = find_abs_id(meta, search_terms)
        print(f"Table: {table} Series ID: {series_id} Units: {units}")

    test_find_abs_id()
