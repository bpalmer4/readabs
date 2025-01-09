"""Get specific ABS data series by searching for the ABS 
data item descriptions."""

# --- imports
# system imports
from typing import Any
import inspect

# Analytic imports
import pandas as pd

# local imports
from readabs.abs_meta_data import metacol as mc
from readabs.search_abs_meta import find_abs_id
from readabs.read_abs_cat import read_abs_cat


# --- private functions
def _work_to_do(wanted: Any) -> bool:
    """Check if there is any work to do."""
    if wanted is None or len(wanted) == 0:
        print("No data requested.")
        return False
    return True


def _wlist_to_wdict(wanted: list[str]) -> dict[str, str]:
    """Convert a list of strings to a dictionary of strings:strings.
    Note: the keys and values are the same.
    Note: any duplicate elements in the list will be lost."""
    return {k: k for k in wanted}


def _get_search_terms(input_dict, output_dict) -> dict[str, str]:
    """Build a selector dictionary from the input dictionary."""
    search_names = {
        abbr: term for abbr, term in inspect.getmembers(mc) if not abbr.startswith("_")
    }
    for mc_abbr, meta_column in search_names.items():
        if mc_abbr in input_dict:
            # the selector dictionary is back-to_front
            # ie. {value_sought: column_name}
            output_dict[input_dict[mc_abbr]] = meta_column
    return output_dict


def _get_args(keys: list[str], input_dict, output_dict) -> dict[str, Any]:
    """Build a retrieval dictionary from the input dictionary."""
    for key in keys:
        if key in input_dict:
            output_dict[key] = input_dict[key]
    return output_dict


def _get_search_args(input_dict: dict, output_dict: dict) -> dict[str, Any]:
    """Extract the search arguments from the input dictionary."""
    keys = ["validate_unique", "exact_match", "regex", "verbose"]
    return _get_args(keys, input_dict, output_dict)


def _get_retrieval_args(input_dict: dict, output_dict: dict) -> dict[str, Any]:
    """Extract the retrieval arguments from the input dictionary."""
    keys = [
        "ignore_errors",
        "get_zip",
        "get_excel_if_no_zip",
        "get_excel",
        "cache_only",
        "single_excel_only",
        "single_zip_only",
        "verbose",
    ]
    return _get_args(keys, input_dict, output_dict)


def _get_item_from_str(
    item: str,
    data_dict,
    data_meta,
    item_selector,
    search_args,
) -> tuple[pd.Series, pd.DataFrame]:
    """Get a data series from the data dictionary and metadata.
    Give the series its series-id as a name."""

    if not data_dict or data_meta.empty:
        raise ValueError(
            "If the wanted data is a string, a populated abs_dict "
            + "and abs_meta must be provided."
        )
    item_selector[item] = mc.did  # back_to_front
    table, series_id, units = find_abs_id(data_meta, item_selector, **search_args)

    series = data_dict[table][series_id]
    series.name = series_id
    series_meta = data_meta.loc[
        (data_meta[mc.table] == table)
        & (data_meta[mc.id] == series_id)
        & (data_meta[mc.unit] == units)
    ]
    return series, series_meta


def _get_item_from_dict(
    item_dict: dict[str, Any],
    data_dict: dict[str, pd.DataFrame],
    data_meta: pd.DataFrame,
    item_selector: dict[str, str],
    search_args: dict[str, Any],
    **kwargs,
) -> tuple[pd.Series, pd.DataFrame]:

    # preparation
    if "did" not in item_dict:
        raise ValueError("Each inner dictionary must contain a 'did' key.")
    item = item_dict.pop("did")
    item_selector = _get_search_terms(item_dict, item_selector)
    item_search_args = _get_search_args(item_dict, search_args)

    if not data_dict or data_meta.empty:
        # data retrieval reqquired
        if "cat" not in item_dict:
            raise ValueError(
                "Each inner dictionary must contain a 'cat' key, "
                + "if an abs_dict is not provided/empty or the "
                + "abs_meta is not provided/empty."
            )
        ret_args = _get_retrieval_args(kwargs, {})
        ret_args = _get_retrieval_args(item_dict, ret_args)
        data_dict, data_meta = read_abs_cat(cat=item_dict["cat"], **ret_args)

    # series extraction based on search terms
    series, series_meta = _get_item_from_str(
        item=item,
        data_dict=data_dict,
        data_meta=data_meta,
        item_selector=item_selector,
        search_args=item_search_args,
    )
    return series, series_meta


# --- public functions
def read_abs_by_desc(
    wanted: list[str] | dict[str, str] | dict[str, dict[str, Any]],
    **kwargs: Any,
) -> tuple[dict[str, pd.Series], pd.DataFrame]:
    """Get specific ABS data series by searching the ABS meta data.

    Parameters
    ----------
    - wanted : list of str, dict of str:str, or dict of str:dict - the data
        item descriptions to search for. If a list, it will be a list of
        descriptions to search for. If a dictionary, the keys will a name.
        The dixtionary values can be either a string (the data item
        description to search for) or a dictionary of keyword arguments, one of
        which would be the data item description to search for.
    - kwargs : Any - keyword arguments to control the data retrieval.
        The keyword arguments can include the following:
        - abs_dict : dict - the dictionary of ABS data to search (from
            read_abs_cat()).
        - abs_meta : DataFrame - the metadata for the ABS data (from
            read_abs_cat()).
        - for the retrieval of data, the "cat" argument must be present.
            The following arguments, if present, will also be used (ie.
            passed to read_abs_cat()): ["ignore_errors", "get_zip",
            "get_excel_if_no_zip", "get_excel", "cache_only",
            "single_excel_only", "single_zip_only", "verbose"].
        - for the selection of data, the following metacol names, if present,
            will be used to construct the selector: "cat", "did"
            "stype", "id", "start", "end", "num", "unit", "dtype", "freq",
            "cmonth", "table", "tdesc".
        - finally, the following arguments will be passed to the find_abs_id()
            and search_abs_meta() functions: ["validate_unique", "exact_match",
            "regex", "verbose"].

    Notes:
    - if "wanted" is of type list[str] or dict[str, str], the kwargs should
        include sufficient keys from the metacol dataclass to get the data.
        Typically, the "cat" key, the "table" key, and the "stype" key would
        be required. The did key would taken from the wanted list or
        dictionary.
    if wanted is of type dict[str, dict[str, Any]], the inner dictionary
        must contain a "did" key. The other keys that can be used for the
        data retrieval are the same as the metacol dataclass fileds, namely:
        "cat", "stype", "id", "start", "end", "num", "unit", "dtype", "freq",
        "cmonth", "table", "tdesc".
    - if abs_dict and abs_meta are provided within the kwargs, they will be
        used to locate and extract the selected data.
    - if abs_dict and abs_meta are not provided, then, (1) wanted must be of
        type dict[str, dict[str, Any]] and (2) the inner dictionary must
        contain a "cat" key so the data can be retrieved. Other keys that
        can be used for the data retrieval are the same as for read_abs_cat(),
        namely ["ignore_errors", "get_zip", "get_excel_if_no_zip",
        "get_excel", "single_excel_only", "single_zip_only", "cache_only"].


    Returns
    -------
    Returns a tuple of two items:
    - A dictionary of pandas Series objects, where the keys are the series
      descriptions. The series.name attribute will be the ABS series-id.
    - A pandas DataFrame containing the metadata for the series.

    Example
    -------

    ```python
    import readabs as ra
    from pandas import DataFrame
    cat_num = "5206.0"  # The ABS National Accounts
    data, meta = ra.read_abs_cat(cat=cat_num)
    wanted = ["Gross domestic product: Chain volume measures ;",]
    selected, selected_meta = ra.read_abs_by_desc(
        wanted=wanted, abs_dict=data, abs_meta=meta, table="5206001_Key_Aggregates"
    )
    ```"""

    # - preparation
    if not _work_to_do(wanted):
        return {}, pd.DataFrame()
    if isinstance(wanted, list):
        wanted = _wlist_to_wdict(wanted)
    abs_dict = kwargs.get("abs_dict", {})
    abs_meta = kwargs.get("abs_meta", pd.DataFrame())
    kwarg_selector = _get_search_terms(kwargs, {})
    search_args = _get_search_args(kwargs, {})

    return_dict = {}
    return_meta = pd.DataFrame()
    for key, value in wanted.items():

        item_selector = kwarg_selector.copy()
        item_search_args = search_args.copy()
        if isinstance(value, str):
            series, meta = _get_item_from_str(
                item=value,
                data_dict=abs_dict,
                data_meta=abs_meta,
                item_selector=item_selector,
                search_args=item_search_args,
            )

        elif isinstance(value, dict):
            series, meta = _get_item_from_dict(
                item_dict=value,
                data_dict=abs_dict,
                data_meta=abs_meta,
                item_selector=item_selector,
                search_args=item_search_args,
                **kwargs,
            )
        else:
            raise TypeError(
                "Each value in the wanted list/dictionary must be either a string "
                + "or a dictionary."
            )

        # save search results
        return_dict[key] = series
        return_meta = pd.concat([return_meta, meta])

    return return_dict, return_meta


# --- testing ---
if __name__ == "__main__":
    # --- test 1: get a list of dids
    def test1():
        """Test case: get a list of dids."""

        cat = "5206.0"
        table = "5206001_Key_Aggregates"
        data_dict, data_meta = read_abs_cat(
            cat=cat, single_excel_only=table, verbose=False
        )
        stype = "Seasonally Adjusted"
        get_these = data_meta.loc[
            (data_meta[mc.table] == table)
            & (data_meta[mc.stype] == stype)
            & data_meta[mc.unit].str.contains("Million")
            & data_meta[mc.did].str.contains("Chain volume measures")
        ][mc.did].to_list()
        print(f"get_these: {get_these}")

        selected, selected_meta = read_abs_by_desc(
            wanted=get_these,
            abs_dict=data_dict,
            abs_meta=data_meta,
            # exact_match=True, verbose=True,
            table=table,
            stype=stype,
        )
        print(selected, selected_meta)

    test1()

    # --- test 2: get a dictionary of dids
    def test2():
        """Test case: get a dictionary of dids."""

        gdp_table = "5206001_Key_Aggregates"
        uer_table = "6202001"
        sa = "Seasonally Adjusted"
        get_these = {
            # two series, each from two different ABS Catalogue Numbers
            "GDP": {
                "cat": "5206.0",
                "table": gdp_table,
                "stype": sa,
                "did": "Gross domestic product: Chain volume measures ;",
                "single_excel_only": gdp_table,
            },
            "Unemployment Rate": {
                "cat": "6202.0",
                "table": uer_table,
                "stype": sa,
                "did": "Unemployment rate ;  Persons ;",
                "single_excel_only": uer_table,
            },
        }
        selected, selected_meta = read_abs_by_desc(
            wanted=get_these,
        )

        print(selected_meta)
        print(selected)

    test2()
