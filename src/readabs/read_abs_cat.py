"""read_abs_cat.py

Download all/selected *timeseries* data from the
Australian Bureau of Statistics (ABS) for a specified 
ABS catalogue identifier and package that data into (1) a 
dictionary of DataFrames and (2) a separate DataFrame of 
meta data.

Note: if you only need data from a single Excel file or a single
zip file, you can specify the stem-name of that file in the keyword
argument 'single_excel_only=' or 'single_zip_only='. For example, the 
stem-name for the first Excel file in the Labour Force Survey is 
'6202001'. Doing this can save substantial time and bandwidth.

This module uses grab_abs_url.py to get the initial data. It then
processes the timeseries data from the ABS website. It makes sure that
dates are converted to an appropriate PeriodIndex, and that the data
is stored in a DataFrame with the correct columns. It also captures
the metadata for each data item."""

# --- imports ---
# standard library imports
from functools import cache
from typing import Any, cast
import calendar

# analytic imports
import pandas as pd
from pandas import DataFrame

# local imports - ugly, need to find out how to fix this
# print(f"in read_abs_cat.py: __main__={__name__}, __package__={__package__}")
if __package__ is None or __package__ == "":
    from abs_meta_data_support import metacol
    from read_support import HYPHEN
    from grab_abs_url import grab_abs_url
else:
    from .abs_meta_data_support import metacol
    from .read_support import HYPHEN
    from .grab_abs_url import grab_abs_url


# --- functions ---
# - public -
@cache  # minimise slowness for any repeat business
def read_abs_cat(
    cat: str,
    keep_non_ts: bool = False,
    **kwargs: Any,
) -> tuple[dict[str, DataFrame], DataFrame]:
    """Read the ABS data for a catalogue id and return the data.

    Parameters
    ----------
    cat : str
        The ABS catalogue number.
    keep_non_ts : bool
        If True, keep non-time series data [default: False].
    **kwargs : Any
        Keyword arguments for the read_abs_cat function.

    Returns
    -------
    tuple[dict[str, DataFrame], DataFrame]
        A dictionary of DataFrames and a DataFrame of the meta data.
        The dictionary is indexed by table names, which can be found
        in the meta data DataFrame."""

    # --- set up ---
    keep_non_ts: bool = kwargs.pop("keep_non_ts", False)

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
    new_dict, meta_data = {}, DataFrame()

    # --- group the sheets and iterate over these groups
    long_groups = _group_sheets(abs_dict)
    for table, sheets in long_groups.items():
        new_dict, meta_data = _capture(
            cat, abs_dict, table, sheets, new_dict, meta_data, **kwargs
        )

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
    cat: str,
    from_dict: dict[str, DataFrame],
    table: str,
    long_sheets: list[str],
    to_dict: dict[str, DataFrame],
    meta_data: DataFrame,
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
    short_sheets = [x.split(HYPHEN, 1)[1] for x in long_sheets]
    try:
        index = short_sheets.index("Index")
    except ValueError:
        print(f"Table {table} has no 'Index' sheet.")
        to_dict = _copy_raw_sheets(from_dict, long_sheets, to_dict, keep_non_ts)
        return to_dict, meta_data

    index_sheet = long_sheets[index]
    this_meta = _capture_meta(cat, from_dict, index_sheet, **kwargs)
    if this_meta.empty:
        to_dict = _copy_raw_sheets(from_dict, long_sheets, to_dict, keep_non_ts)
        return to_dict, meta_data

    meta_data = pd.concat([meta_data, this_meta], axis=0)

    # --- step 2: capture the actual time series data ---
    data = _capture_data(meta_data, from_dict, long_sheets, **kwargs)
    if len(data):
        to_dict[table] = data
    else:
        # a glitch: we have the metadata but not the actual data
        error = f"Unexpected: {table} has no actual data."
        if not ignore_errors:
            raise ValueError(error)
        print(error)
        to_dict = _copy_raw_sheets(from_dict, long_sheets, to_dict, keep_non_ts)

    return to_dict, meta_data


def _capture_data(
    abs_meta: DataFrame,
    from_dict: dict[str, DataFrame],
    long_sheets: list[str],
    **kwargs: Any,
) -> DataFrame:
    """Take a list of ABS data sheets and put them into a single DataFrame."""

    # --- step 0: set up ---
    verbose: bool = kwargs.get("verbose", False)
    merged_data = DataFrame()

    # --- step 1: capture the time series data ---
    # identify the data sheets in the list of all sheets from Excel file
    data_sheets = [x for x in long_sheets if x.split(HYPHEN, 1)[1].startswith("Data")]

    for sheet_name in data_sheets:
        # --- capture just the data, nothing else
        sheet_data = from_dict[sheet_name].copy()
        # get the columns
        header = sheet_data.iloc[8]
        sheet_data.columns = header
        sheet_data = sheet_data[9:]
        # get the row indexes - assume long row names are not dates
        index_column = sheet_data[sheet_data.columns[0]].astype(str)
        sheet_data = sheet_data.drop(sheet_data.columns[0], axis=1)
        long_row_names = index_column.str.len() > 20  # 19 chars in datetime str
        if verbose and long_row_names.any():
            print(f"You may need to check index column for {sheet_name}")
        index_column = index_column.loc[~long_row_names]
        sheet_data = sheet_data.loc[~long_row_names]
        sheet_data.index = pd.to_datetime(index_column) #
        # further clearning
        sheet_data = sheet_data.dropna(how="all", axis=0)  # remobe na rows

        # get the correct period index
        short_name = sheet_name.split(HYPHEN, 1)[0]
        series_id = sheet_data.columns[0]
        freq = (
            abs_meta[abs_meta[metacol.table] == short_name]
            .at[series_id, metacol.freq]
            .upper()
            .strip()
            [0]
        )
        freq = "Y" if freq == "A" else freq  # pandas prefers yearly
        freq = "Q" if freq == "B" else freq  # treat Biannual as quarterly
        # create an appropriate period index
        if freq:
            if freq in ("Q", "Y"):
                month = calendar.month_abbr[
                    cast(pd.PeriodIndex, sheet_data.index).month.max()
                ].upper()
                freq = f"{freq}-{month}"
            if isinstance(sheet_data.index, pd.DatetimeIndex):
                sheet_data = sheet_data.to_period(freq=freq)

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


def _capture_meta(
    cat: str,
    from_dict: dict[str, DataFrame],
    index_sheet: str,
    **kwargs: Any,
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
    file_meta.columns = header_columns

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
    file_meta.index = file_meta[metacol.id]

    return file_meta


def _group_sheets(
    abs_dict: dict[str, DataFrame],
) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """Group the sheets from an Excel file."""

    keys = list(abs_dict.keys())
    long_pairs = [[x.split(HYPHEN, 1)[0], x] for x in keys]

    def group(p_list: list[str, str]) -> dict[str, list[str]]:
        groups = {}
        for x, y in p_list:
            if x not in groups:
                groups[x] = []
            groups[x].append(y)
        return groups

    return group(long_pairs)


# --- initial testing ---
if __name__ == "__main__":
    d, m = read_abs_cat("6202.0", single_excel_only="6202001")

    print(m.columns)
    print(m["Table Description"].unique())
    print(m.tail())

    print(d.keys())
    print(d["6202001"].index.dtype)
    print(d["6202001"].dtypes)
    print(d["6202001"].head())
    print(d["6202001"].tail())
