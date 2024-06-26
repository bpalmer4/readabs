"""read_abs_cat.py

Download all/selected timeseries data from the
Australian Bureau of Statistics (ABS) for a specified 
ABS catalogue identifier and package that data into a 
dictionary of DataFrames."""

# --- imports ---
# standard library imports
import calendar
import zipfile
from functools import cache
from io import BytesIO
from typing import Any, Callable, cast

# analytic imports
import pandas as pd
from pandas import DataFrame

# local imports - ugly, need to find out how to fix this
# print(f"in read_abs_cat.py: __main__={__name__}, __package__={__package__}")
if __package__ is None or __package__ == "":
    from abs_meta_data_support import metacol
    from get_data_links import get_data_links, get_table_name
    from abs_catalogue_map import catalogue_map
    from read_support import check_kwargs, get_args
    from download_cache import get_file
else:
    from .abs_meta_data_support import metacol
    from .get_data_links import get_data_links, get_table_name
    from .abs_catalogue_map import catalogue_map
    from .read_support import check_kwargs, get_args
    from .download_cache import get_file


# --- functions ---
# private
def _get_meta_from_excel(
    excel: pd.ExcelFile,
    table: str,
    tab_desc: str,
    cat_id: str,
) -> pd.DataFrame:
    """Capture the metadata from the Index sheet of an ABS excel file.
    Returns a DataFrame specific to the current excel file.
    Returning an empty DataFrame, means that the meatadata could not
    be identified. Meta data for each ABS data item is organised by row."""

    # Unfortunately, the header for some of the 3401.0
    #                spreadsheets starts on row 10
    starting_rows = 9, 10
    required = metacol.did, metacol.id, metacol.stype, metacol.unit
    required_set = set(required)
    for header_row in starting_rows:
        file_meta = excel.parse(
            "Index",
            header=header_row,
            parse_dates=True,
            infer_datetime_format=True,
            converters={"Unit": str},
        )
        file_meta = file_meta.iloc[1:-2]  # drop first and last 2
        file_meta = file_meta.dropna(axis="columns", how="all")

        if required_set.issubset(set(file_meta.columns)):
            break

        if header_row == starting_rows[-1]:
            print(f"Could not find metadata for {cat_id}-{tab_desc}")
            return pd.DataFrame()

    # add the table name and table description to the metadata
    file_meta[metacol.table] = table.strip()
    file_meta[metacol.tdesc] = tab_desc.strip()
    file_meta[metacol.cat] = cat_id.strip()

    # make damn sure there are no rogue white spaces
    for col in required:
        file_meta[col] = file_meta[col].str.strip()

    return file_meta


# private
def _unpack_excel_into_df(
    excel: pd.ExcelFile,
    meta: DataFrame,
    freq: str,
    verbose: bool,
) -> DataFrame:
    """Take an ABS excel file and put all the Data sheets into a single
    pandas DataFrame and return that DataFrame."""

    data = DataFrame()
    data_sheets = [x for x in excel.sheet_names if cast(str, x).startswith("Data")]
    for sheet_name in data_sheets:
        sheet_data = excel.parse(
            sheet_name,
            header=9,
            index_col=0,
        ).dropna(how="all", axis="index")
        data.index = pd.to_datetime(data.index)

        # merge data into a large dataframe
        if len(data) == 0:
            data = sheet_data
        else:
            data = pd.merge(
                left=data,
                right=sheet_data,
                how="outer",
                left_index=True,
                right_index=True,
                suffixes=("", ""),
            )
    if freq:
        if freq in ("Q", "A"):
            month = calendar.month_abbr[
                cast(pd.PeriodIndex, data.index).month.max()
            ].upper()
            freq = f"{freq}-{month}"
        if isinstance(data.index, pd.DatetimeIndex):
            data = data.to_period(freq=freq)

    # check for NA columns - rarely happens
    # Note: these empty columns are not removed,
    # but it is useful to know they are there
    if data.isna().all().any() and verbose:
        cols = data.columns[data.isna().all()]
        print(
            "Caution: these columns are all NA in "
            + f"{meta[metacol.table].iloc[0]}: {cols}"
        )

    # check for duplicate columns - should not happen
    # Note: these duplicate columns are removed
    duplicates = data.columns.duplicated()
    if duplicates.any():
        if verbose:
            dup_table = meta[metacol.table].iloc[0]
            print(
                f"Note: duplicates removed from {dup_table}: "
                + f"{data.columns[duplicates]}"
            )
        data = data.loc[:, ~duplicates].copy()
    return data


# private
def _extract_data_from_excel(
    raw_bytes: bytes, table_name: str, **kwargs: Any
) -> tuple[DataFrame, DataFrame]:
    """Convert the raw bytes of an Excel file into a pandas DataFrame.
    Returns the actual data and meta data in two separate DataFrames."""

    ignore_errors = kwargs.get("ignore_errors", False)

    # convert the raw bytes into a pandas ExcelFile
    try:
        excel = pd.ExcelFile(BytesIO(raw_bytes))
    except Exception as e:
        message = f"With {table_name}: could not convert raw bytes to ExcelFile.\n{e}"
        if ignore_errors:
            print(message)
            return pd.DataFrame(), pd.DataFrame()
        raise RuntimeError(message) from e

    excel = pd.ExcelFile(BytesIO(raw_bytes))

    # get table information (ie. the meta data)
    if "Index" not in excel.sheet_names:
        print(
            "Caution: Could not find the 'Index' "
            f"sheet in {table_name}. File not included"
        )
        return pd.DataFrame(), pd.DataFrame()

    # get table header information
    header = excel.parse("Index", nrows=8)  # ???
    cat_id = header.iat[3, 1].split(" ")[0].strip()
    tab_desc = header.iat[4, 1].split(".", 1)[-1].strip()

    # get the metadata rows
    file_meta = _get_meta_from_excel(excel, table_name, tab_desc, cat_id)
    if len(file_meta) == 0:
        return pd.DataFrame(), pd.DataFrame()

    # establish freq - used for making the index a PeriodIndex
    freq_dict = {"annual": "Y", "biannual": "Q", "quarter": "Q", "month": "M"}
    freqlist = file_meta["Freq."].str.lower().unique()
    if not len(freqlist) == 1 or freqlist[0] not in freq_dict:
        print(f"Unrecognised data frequency {freqlist} for {tab_desc}")
        return pd.DataFrame(), pd.DataFrame()
    freq = freq_dict[freqlist[0]]

    data = _unpack_excel_into_df(
        excel, file_meta, freq, verbose=kwargs.get("verbose", False)
    )

    return data, file_meta


# private
def _process_zip_binary(
    zip_contents: bytes,
    **kwargs: Any,
) -> tuple[dict[str, DataFrame], DataFrame]:
    """Extract the contents of a ZIP file into a tuple, where the
    first element is a dictionary of DataFrames; and the second
    element is the related ABS meta data in a DataFrame."""

    verbose = kwargs.get("verbose", False)
    if verbose:
        print("Extracting DataFrames from the zip-file binary.")
    returnable_data: dict[str, DataFrame] = {}
    returnable_meta = DataFrame()

    with zipfile.ZipFile(BytesIO(zip_contents)) as zipped:
        for count, element in enumerate(zipped.infolist()):
            # get the zipfile into pandas
            table_name = get_table_name(url=element.filename)
            raw_bytes = zipped.read(element.filename)
            excel_df, file_meta = _extract_data_from_excel(
                raw_bytes, table_name, **kwargs
            )
            if len(excel_df) == 0:
                # this table could not be captured
                continue

            # fix tabulation if ABS used the same table numbers for data
            if table_name in returnable_data:
                # This really just should not happen, but if it does, we need to dix it
                tmp = f"{table_name}-{count}"
                if verbose:
                    print(f"Changing duplicate table name from {table_name} to {tmp}.")
                table_name = tmp
                file_meta[metacol.table] = table_name

            # aggregate the meta data
            returnable_meta = pd.concat([returnable_meta, file_meta])

            # add the table to the returnable dictionary
            returnable_data[table_name] = excel_df

    return returnable_data, returnable_meta


# private
def _add_zip(
    link: str, abs_dict: dict[str, DataFrame], abs_meta: DataFrame, **args
) -> tuple[dict[str, DataFrame], DataFrame]:
    """Add tables from zip file to the dictionary of DataFrames
    and associated rows to the meta data."""

    zip_contents = get_file(link, **args)
    if len(zip_contents) == 0:
        return abs_dict, abs_meta
    zip_data, zip_meta = _process_zip_binary(zip_contents, **args)
    abs_dict.update(zip_data)
    abs_meta = pd.concat([abs_meta, zip_meta], axis=0)
    return abs_dict, abs_meta


# private
def _add_excel(
    link: str,
    abs_dict: dict[str, DataFrame],
    abs_meta: DataFrame,
    **args: Any,
) -> tuple[dict[str, DataFrame], DataFrame]:
    """Add a table to the dictionary of DataFrames
    and rows to the the meta data."""

    name = get_table_name(link)
    if name in abs_dict:
        # table already in the dictionary
        return abs_dict, abs_meta
    raw_bytes = get_file(link, **args)
    if len(raw_bytes) == 0:
        # could not get the file, and errors are ignored
        return abs_dict, abs_meta
    excel_df, file_meta = _extract_data_from_excel(raw_bytes, name, **args)
    if len(excel_df) == 0:
        # could not get the file, and errors are ignored
        return abs_dict, abs_meta
    abs_dict[name] = excel_df
    abs_meta = pd.concat([abs_meta, file_meta], axis=0)
    return abs_dict, abs_meta


# private
def _add_single(
    name: str,
    abs_dict: dict[str, DataFrame],
    abs_meta: DataFrame,
    links: dict[str, list[str]],
    typology: str,  # ".zip" or ".xlsx"
    **args,
) -> tuple[dict[str, DataFrame], DataFrame]:
    """Add a single excel file or zip file to the dictionary of DataFrames,
    along with associated meta data."""

    fn: Callable = _add_zip if typology == ".zip" else _add_excel
    selection = {get_table_name(x): x for x in links.get(typology, [])}
    if name not in selection:
        message = f"File ({name}{typology}) not found on ABS web page."
        if not args["ignore_errors"]:
            raise ValueError(message)
        print(message)
        return abs_dict, abs_meta
    abs_dict, abs_meta = fn(selection[name], abs_dict, abs_meta, **args)
    return abs_dict, abs_meta


# public -- primary entry point for this module
@cache  # minimise slowness with repeat business
def read_abs_cat(
    cat: str, **kwargs: Any  # ABS catalogue number  # keyword arguments
) -> tuple[dict[str, DataFrame], DataFrame]:
    """Read the ABS data for a catalogue id and return the data.

    Parameters
    ----------
    cat : str
        The ABS catalogue number.
    **kwargs : Any
        Keyword arguments for the read_abs_cat function.

    Returns
    -------
    tuple[dict[str, DataFrame], DataFrame]
        A dictionary of DataFrames and a DataFrame of the meta data.
        The dictionary is indexed by table names, which can be found
        in the meta data DataFrame."""

    # check/get the keyword arguments
    check_kwargs(kwargs, "read_abs_cat")
    args = get_args(kwargs)

    if (
        not args["get_zip"]
        and not args["get_excel"]
        and not args["get_excel_if_no_zip"]
    ):
        raise ValueError("read_abs_dict: either get_zip or get_excel must be True.")

    # convert the catalogue number to the ABS webpage URL
    cm = catalogue_map()
    if cat not in cm.index:
        raise ValueError(f"ABS catalogue number {cat} not found.")
    url = cm["URL"].astype(str)[cat]

    # get the URL links to the relevant ABS data files on that webpage
    links = get_data_links(url, **args)
    if not links:
        print(f"No data files found for catalogue number {cat}")
        return {}, DataFrame()  # return an empty dictionary, DataFrame

    # read the data files into a dictionary of DataFrames
    abs_dict: dict[str, DataFrame] = {}
    abs_meta: DataFrame = DataFrame()

    if args["single_excel_only"]:
        abs_dict, abs_meta = _add_single(
            args["single_excel_only"], abs_dict, abs_meta, links, ".xlsx", **args
        )

    elif args["single_zip_only"]:
        abs_dict, abs_meta = _add_single(
            args["single_zip_only"], abs_dict, abs_meta, links, ".zip", **args
        )

    else:
        for link_type in ".zip", ".xlsx":  # .zip must come first
            for link in links.get(link_type, []):
                if link_type == ".zip" and args["get_zip"]:
                    abs_dict, abs_meta = _add_zip(link, abs_dict, abs_meta, **args)

                elif link_type == ".xlsx" and (
                    args["get_excel"]
                    or (args["get_excel_if_no_zip"] and not args["get_zip"])
                    or (args["get_excel_if_no_zip"] and not links.get(".zip", []))
                ):
                    abs_dict, abs_meta = _add_excel(
                        link, abs_dict, abs_meta, links=links, **args
                    )

    # reset the index of the metadata
    return abs_dict, abs_meta.reset_index()
