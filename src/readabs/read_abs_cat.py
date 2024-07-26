"""Download *timeseries* data from the Australian Bureau 
of Statistics (ABS) for a specified ABS catalogue identifier."""

# --- imports ---
# standard library imports
from functools import cache
from typing import Any
import calendar

# analytic imports
import pandas as pd
from pandas import DataFrame

# local imports
from readabs.abs_meta_data import metacol
from readabs.read_support import HYPHEN
from readabs.grab_abs_url import grab_abs_url


# --- functions ---
# - public -
@cache  # minimise slowness for any repeat business
def read_abs_cat(
    cat: str,
    keep_non_ts: bool = False,
    **kwargs: Any,
) -> tuple[dict[str, DataFrame], DataFrame]:
    """This function returns the complete ABS Catalogue information as a
    python dictionary of pandas DataFrames, as well as the associated metadata
    in a separate DataFrame. The function automates the collection of zip and
    excel files from the ABS website. If necessary, these files are downloaded,
    and saved into a cache directory. The files are then parsed to extract time
    series data, and the associated metadata.

    By default, the cache directory is `./.readabs_cache/`. You can change the
    default directory name by setting the shell environment variable
    `READABS_CACHE_DIR` with the name of the preferred directory.

    Parameters
    ----------

    cat : str
        The ABS Catalogue Number for the data to be downloaded and made
        available by this function. This argument must be specified in the
        function call.

    keep_non_ts : bool = False
        A flag for whether to keep the non-time-series tables
        that might form part of an ABS catalogue item. Normally, the
        non-time-series information is ignored, and not made available to
        the user.

    **kwargs : Any
        The following parameters may be passed as optional keyword arguments.

    history : str = ""
        Orovide a month-year string to extract historical ABS data.
        For example, you can set history="dec-2023" to the get the ABS data
        for a catalogue identifier that was originally published in respect
        of Q4 of 2023. Note: not all ABS data sources are structured so that
        this technique works in every case; but most are.

    verbose : bool = False
        Setting this to true may help diagnose why something
        might be going wrong with the data retrieval process.

    ignore_errors : bool = False
        Normally, this function will cease downloading when
        an error in encountered. However, sometimes the ABS website has
        malformed links, and changing this setting is necessitated. (Note:
        if you drop a message to the ABS, they will usually fix broken
        links with a business day).

    get_zip : bool = True
        Download the excel files in .zip files.

    get_excel_if_no_zip : bool = True
        Only try to download .xlsx files if there are no zip
        files available to be downloaded. Only downloading individual excel
        files when there are no zip files to download can speed up the
        download process.

    get_excel : bool = False
        The default value means that excel files are not
        automatically download. Note: at least one of `get_zip`,
        `get_excel_if_no_zip`, or `get_excel` must be true. For most ABS
        catalogue items, it is sufficient to just download the one zip
        file. But note, some catalogue items do not have a zip file.
        Others have quite a number of zip files.

    single_excel_only : str = ""
        If this argument is set to a table name (without the
        .xlsx extension), only that excel file will be downloaded. If
        set, and only a limited subset of available data is needed,
        this can speed up download times significantly. Note: overrides
        `get_zip`, `get_excel_if_no_zip`, `get_excel` and `single_zip_only`.

    single_zip_only : str = ""
        If this argument is set to a zip file name (without
        the .zip extension), only that zip file will be downloaded.
        If set, and only a limited subset of available data is needed,
        this can speed up download times significantly. Note: overrides
        `get_zip`, `get_excel_if_no_zip`, and `get_excel`.

    cache_only : bool = False
        If set to True, this function will only access
        data that has been previously cached. Normally, the function
        checks the date of the cache data against the date of the data
        on the ABS website, before deciding whether the ABS has fresher
        data that needs to be downloaded to the cache.

    Returns
    -------------
    tuple[dict[str, DataFrame], DataFrame]
        The function returns a tuple of two items. The first item is a
        python dictionary of pandas DataFrames (which is the primary data
        associated with the ABS catalogue item). The second item is a
        DataFrame of ABS metadata for the ABS collection.

    Example
    -------

    ```python
    import readabs as ra
    from pandas import DataFrame
    cat_num = "6202.0"  # The ABS labour force survey
    data: tuple[dict[str, DataFrame], DataFrame] = ra.read_abs_cat(cat=cat_num)
    abs_dict, meta = data
    ```"""

    # --- get the time series data ---
    raw_abs_dict = grab_abs_url(cat=cat, **kwargs)
    abs_dict, abs_meta = _get_time_series_data(
        cat, raw_abs_dict, keep_non_ts=keep_non_ts, **kwargs
    )

    return abs_dict, abs_meta


# - private -
def _get_time_series_data(
    cat: str,
    abs_dict: dict[str, DataFrame],
    **kwargs: Any,
) -> tuple[dict[str, DataFrame], DataFrame]:
    """Using the raw DataFrames from the ABS website, extract the time series
    data for a specific ABS catalogue identifier. The data is returned in a
    tuple. The first element is a dictionary of DataFrames, where each
    DataFrame contains the time series data. The second element is a DataFrame
    of meta data, which describes each data item in the dictionary"""

    # --- set up ---
    new_dict: dict[str, DataFrame] = {}
    meta_data = DataFrame()

    # --- group the sheets and iterate over these groups
    long_groups = _group_sheets(abs_dict)
    for table, sheets in long_groups.items():
        args = {
            "cat": cat,
            "from_dict": abs_dict,
            "table": table,
            "long_sheets": sheets,
        }
        new_dict, meta_data = _capture(new_dict, meta_data, args, **kwargs)
    return new_dict, meta_data


def _copy_raw_sheets(
    from_dict: dict[str, DataFrame],
    long_sheets: list[str],
    to_dict: dict[str, DataFrame],
    keep_non_ts,
) -> dict[str, DataFrame]:
    """A utility function to copy the raw sheets across to
    the final dictionary. Used if the data is not in a
    timeseries format, and keep_non_ts flag is set to True.
    Returns an updated final dictionary."""

    if not keep_non_ts:
        return to_dict

    for sheet in long_sheets:
        if sheet in from_dict:
            to_dict[sheet] = from_dict[sheet]
        else:
            # should not happen
            raise ValueError(f"Glitch: Sheet {sheet} not found in the data.")
    return to_dict


def _capture(
    to_dict: dict[str, DataFrame],
    meta_data: DataFrame,
    args: dict[str, Any],
    **kwargs: Any,
) -> tuple[dict[str, DataFrame], DataFrame]:
    """For a specific Excel file, capture *both* the time series data
    from the ABS data files as well as the meta data. These data are
    added to the input 'to_dict" and 'meta_data' respectively, and
    the combined results are returned as a tuple."""

    # --- step 0: set up ---
    keep_non_ts: bool = kwargs.get("keep_non_ts", False)
    ignore_errors: bool = kwargs.get("ignore_errors", False)

    # --- step 1: capture the meta data ---
    short_names = [x.split(HYPHEN, 1)[1] for x in args["long_sheets"]]
    if "Index" not in short_names:
        print(f"Table {args["table"]} has no 'Index' sheet.")
        to_dict = _copy_raw_sheets(
            args["from_dict"], args["long_sheets"], to_dict, keep_non_ts
        )
        return to_dict, meta_data
    index = short_names.index("Index")

    index_sheet = args["long_sheets"][index]
    this_meta = _capture_meta(args["cat"], args["from_dict"], index_sheet)
    if this_meta.empty:
        to_dict = _copy_raw_sheets(
            args["from_dict"], args["long_sheets"], to_dict, keep_non_ts
        )
        return to_dict, meta_data

    meta_data = pd.concat([meta_data, this_meta], axis=0)

    # --- step 2: capture the actual time series data ---
    data = _capture_data(meta_data, args["from_dict"], args["long_sheets"], **kwargs)
    if len(data):
        to_dict[args["table"]] = data
    else:
        # a glitch: we have the metadata but not the actual data
        error = f"Unexpected: {args["table"]} has no actual data."
        if not ignore_errors:
            raise ValueError(error)
        print(error)
        to_dict = _copy_raw_sheets(
            args["from_dict"], args["long_sheets"], to_dict, keep_non_ts
        )

    return to_dict, meta_data


def _capture_data(
    abs_meta: DataFrame,
    from_dict: dict[str, DataFrame],
    long_sheets: list[str],
    **kwargs: Any,
) -> DataFrame:
    """Take a list of ABS data sheets, find the DataFrames for those sheets in the
    from_dict, and stitch them into a single DataFrame with an appropriate
    PeriodIndex."""

    # --- step 0: set up ---
    verbose: bool = kwargs.get("verbose", False)
    merged_data = DataFrame()
    header_row: int = 8

    # --- step 1: capture the time series data ---
    # identify the data sheets in the list of all sheets from Excel file
    data_sheets = [x for x in long_sheets if x.split(HYPHEN, 1)[1].startswith("Data")]

    for sheet_name in data_sheets:
        if verbose:
            print(f"About to cature data from {sheet_name=}")

        # --- capture just the data, nothing else
        sheet_data = from_dict[sheet_name].copy()

        # get the columns
        header = sheet_data.iloc[header_row]
        sheet_data.columns = pd.Index(header)
        sheet_data = sheet_data[(header_row + 1) :]

        # get the row indexes
        sheet_data = _index_to_period(sheet_data, sheet_name, abs_meta, verbose)

        # --- merge data into a single dataframe
        if len(merged_data) == 0:
            merged_data = sheet_data
        else:
            merged_data = pd.merge(
                left=merged_data,
                right=sheet_data,
                how="outer",
                left_index=True,
                right_index=True,
                suffixes=("", ""),
            )

    # --- step 2 - final tidy-ups
    # remove NA rows
    merged_data = merged_data.dropna(how="all")
    # check for NA columns - rarely happens
    # Note: these empty columns are not removed,
    # but it is useful to know they are there
    if merged_data.isna().all().any() and verbose:
        cols = merged_data.columns[merged_data.isna().all()]
        print(
            "Caution: these columns are all NA in "
            + f"{merged_data[metacol.table].iloc[0]}: {cols}"
        )

    # check for duplicate columns - should not happen
    # Note: these duplicate columns are removed
    duplicates = merged_data.columns.duplicated()
    if duplicates.any():
        if verbose:
            dup_table = abs_meta[metacol.table].iloc[0]
            print(
                f"Note: duplicates removed from {dup_table}: "
                + f"{merged_data.columns[duplicates]}"
            )
        merged_data = merged_data.loc[:, ~duplicates].copy()

    # make the data all floats.
    merged_data = merged_data.astype(float).sort_index()

    return merged_data


def _index_to_period(
    sheet_data: DataFrame, sheet_name: str, abs_meta: DataFrame, verbose: bool
) -> DataFrame:
    """Convert the index of a DataFrame to a PeriodIndex."""

    index_column = sheet_data[sheet_data.columns[0]].astype(str)
    sheet_data = sheet_data.drop(sheet_data.columns[0], axis=1)
    long_row_names = index_column.str.len() > 20  # 19 chars in datetime str
    if verbose and long_row_names.any():
        print(f"You may need to check index column for {sheet_name}")
    index_column = index_column.loc[~long_row_names]
    sheet_data = sheet_data.loc[~long_row_names]

    proposed_index = pd.to_datetime(index_column)  #

    # get the correct period index
    short_name = sheet_name.split(HYPHEN, 1)[0]
    series_id = sheet_data.columns[0]
    freq = (
        abs_meta[abs_meta[metacol.table] == short_name]
        .at[series_id, metacol.freq]
        .upper()
        .strip()[0]
    )
    freq = "Y" if freq == "A" else freq  # pandas prefers yearly
    freq = "Q" if freq == "B" else freq  # treat Biannual as quarterly
    if freq not in ("Y", "Q", "M", "D"):
        print(f"Check the frequency of the data in sheet: {sheet_name}")

    # create an appropriate period index
    if freq:
        if freq in ("Q", "Y"):
            month = calendar.month_abbr[proposed_index.dt.month.max()].upper()
            freq = f"{freq}-{month}"
        sheet_data.index = pd.PeriodIndex(proposed_index, freq=freq)
    else:
        raise ValueError(f"With sheet {sheet_name} could not determime PeriodIndex")

    return sheet_data


def _capture_meta(
    cat: str,
    from_dict: dict[str, DataFrame],
    index_sheet: str,
) -> DataFrame:
    """Capture the metadata from the Index sheet of an ABS excel file.
    Returns a DataFrame specific to the current excel file.
    Returning an empty DataFrame, means that the meta data could not
    be identified. Meta data for each ABS data item is organised by row."""

    # --- step 0: set up ---
    frame = from_dict[index_sheet]

    # --- step 1: check if the metadata is present in the right place ---
    # Unfortunately, the header for some of the 3401.0
    #                spreadsheets starts on row 10
    starting_rows = 8, 9, 10
    required = metacol.did, metacol.id, metacol.stype, metacol.unit
    required_set = set(required)
    all_good = False
    for header_row in starting_rows:
        header_columns = frame.iloc[header_row]
        if required_set.issubset(set(header_columns)):
            all_good = True
            break

    if not all_good:
        print(f"Table has no metadata in sheet {index_sheet}.")
        return DataFrame()

    # --- step 2: capture the metadata ---
    file_meta = frame.iloc[header_row + 1 :].copy()
    file_meta.columns = pd.Index(header_columns)

    # make damn sure there are no rogue white spaces
    for col in required:
        file_meta[col] = file_meta[col].str.strip()

    # remove empty columns and rows
    file_meta = file_meta.dropna(how="all", axis=1).dropna(how="all", axis=0)

    # populate the metadata
    file_meta[metacol.table] = index_sheet.split(HYPHEN, 1)[0]
    tab_desc = frame.iat[4, 1].split(".", 1)[-1].strip()
    file_meta[metacol.tdesc] = tab_desc
    file_meta[metacol.cat] = cat

    # drop last row - should just be copyright statement
    file_meta = file_meta.iloc[:-1]

    # set the index to the series_id
    file_meta.index = pd.Index(file_meta[metacol.id])

    return file_meta


def _group_sheets(
    abs_dict: dict[str, DataFrame],
) -> dict[str, list[str]]:
    """Group the sheets from an Excel file."""

    keys = list(abs_dict.keys())
    long_pairs = [(x.split(HYPHEN, 1)[0], x) for x in keys]

    def group(p_list: list[tuple[str, str]]) -> dict[str, list[str]]:
        groups: dict[str, list[str]] = {}
        for x, y in p_list:
            if x not in groups:
                groups[x] = []
            groups[x].append(y)
        return groups

    return group(long_pairs)


# --- initial testing ---
if __name__ == "__main__":

    def simple_test():
        """A simple test of the read_abs_cat function."""

        # ABS Catalogue ID 8731.0 has a mix of time
        # series and non-time series data. Also,
        # it has unusually structured Excel files. So, a good test.

        print("Starting test.")

        d, _m = read_abs_cat("8731.0", keep_non_ts=False, verbose=False)
        print(f"--- {len(d)=} ---")
        print(f"--- {d.keys()=} ---")
        for table in d.keys():
            print(f"{table=} {d[table].shape=} {d[table].index.freqstr=}")

        print("Test complete.")

    simple_test()
