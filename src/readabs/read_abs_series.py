"""Get specific ABS data series by their ABS series identifiers."""

# --- imports
# system imports
from typing import Any, Sequence, cast

# analytic imports
from pandas import DataFrame, Index, PeriodIndex, concat

# local imports
from readabs.read_abs_cat import read_abs_cat
from readabs.read_support import check_kwargs, get_args
from readabs.abs_meta_data import metacol


# --- functions
def read_abs_series(
    cat: str,
    series_id: str | Sequence[str],
    **kwargs: Any,
) -> tuple[DataFrame, DataFrame]:
    """Get specific ABS data series by their ABS catalogue and series identifiers.

    Parameters
    ----------
    cat : str
        The ABS catalogue ID.

    series_id : str | Sequence[str]
        An ABS series ID or a sequence of ABS series IDs.

    **kwargs : Any
        Keyword arguments for the read_abs_series function,
        which are the same as the keyword arguments for the
        read_abs_cat function.

    Returns
    -------
    tuple[DataFrame, DataFrame]
        A tuple of two DataFrames, one for the primary data and one for the metadata.

    Example
    -------

    ```python
    import readabs as ra
    from pandas import DataFrame
    cat_num = "6202.0"  # The ABS labour force survey
    unemployment_rate = "A84423050A"
    seo = "6202001"  # The ABS table name
    data, meta = ra.read_abs_series(
        cat=cat_num, series_id=unemployment_rate, single_excel_only=seo
    )
    ```"""

    # check for unexpected keyword arguments/get defaults
    check_kwargs(kwargs, "read_abs_series")
    args = get_args(kwargs, "read_abs_series")

    # read the ABS category data
    cat_data, cat_meta = read_abs_cat(cat, **args)

    # drop repeated series_ids in the meta data,
    # make unique series_ids the index
    cat_meta.index = Index(cat_meta[metacol.id])
    cat_meta = cat_meta.groupby(cat_meta.index).first()

    # get the ABS series data
    if isinstance(series_id, str):
        series_id = [series_id]
    return_data, return_meta = DataFrame(), DataFrame()
    for identifier in series_id:

        # confirm that the series ID is in the catalogue
        if identifier not in cat_meta.index:
            if args["verbose"]:
                print(f"Series ID {identifier} not found in ABS catalogue ID {cat}")
            if args["ignore_errors"]:
                continue
            raise ValueError(f"Series ID {identifier} not found in catalogue {cat}")

        # confirm thay the index of the series is compatible
        table = str(cat_meta.loc[identifier, metacol.table])  # str for mypy
        data_series = cat_data[table][identifier]
        if (
            len(return_data) > 0
            and cast(PeriodIndex, return_data.index).freq
            != cast(PeriodIndex, data_series.index).freq
        ):
            if args["verbose"]:
                print(f"Frequency mismatch for series ID {identifier}")
            if args["ignore_errors"]:
                continue
            raise ValueError(f"Frequency mismatch for series ID {identifier}")

        # add the series data and meta data to the return values
        if len(return_data) > 0:
            return_data = return_data.reindex(
                return_data.index.union(data_series.index)
            )
        return_data[identifier] = data_series
        return_meta = concat([return_meta, cat_meta.loc[identifier]], axis=1)

    return return_data, return_meta.T


if __name__ == "__main__":

    def simple_test() -> None:
        """Simple test of the read_abs_series function."""
        # simple test
        # Trimmed Mean - through the year CPI growth - seasonally adjusted
        data, meta = read_abs_series("6401.0", "A3604511X", single_excel_only="640106")
        print(data.tail())
        print(meta.T)
        print("Done")

    simple_test()
