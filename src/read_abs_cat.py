"""Download timeseries data from the
Australian Bureau of Statistics (ABS)
and package that data into DataFrames."""

# --- imports ---
# standard library imports
import calendar
import re
import zipfile
from functools import cache
from io import BytesIO
from typing import Any, cast

# analytic imports
import pandas as pd
from pandas import DataFrame
from bs4 import BeautifulSoup

# local imports
from abs_meta_data_support import metacol
from abs_catalogue_map import catalogue_map
from get_url_cache import get_file, HttpError, CacheError


# --- functions ---
# private
def _make_absolute_url(
    url: str,
) -> str:
    """Convert a relative URL address found on the ABS site to
    an absolute URL address."""

    prefix = "https://www.abs.gov.au"
    # remove a prefix if it already exists (just to be sure)
    url = url.replace(prefix, "")
    url = url.replace(prefix.replace("https://", "http://"), "")
    # add the prefix (back) ...
    return f"{prefix}{url}"


# private
def _get_table_name(url: str) -> str:
    """Get the table name from the ABS URL."""

    tail = url.rsplit("/", 1)[-1]
    table_name = tail.split(".")[0]
    return table_name


# public
@cache
def get_data_links(
    url: str,
    inspect_file_name="",  # for debugging - save the page to disk
    **kwargs,
) -> dict[str, list[str]]:
    """Scan the webpage at the ABS URL for links to ZIP files and for
    links to Microsoft Excel files. 
    Return the links in a dictionary of lists by file type ending. 
    Ensure relative links have been fully expanded."""

    # get relevant web-page from ABS website
    verbose = kwargs.get("verbose", False)
    if verbose:
        print("Getting data links from ABS.")
    try:
        page = get_file(url, **kwargs)
    except (HttpError, CacheError) as e:
        print(f"Error when obtaining links from ABS web page: {e}")
        return {}

    # save the page to disk for inspection
    if inspect_file_name:
        with open(inspect_file_name, "w") as file_handle:
            file_handle.write(page.decode("utf-8"))

    # remove those pesky span tags - probably not necessary
    page = re.sub(b"<span[^>]*>", b" ", page)
    page = re.sub(b"</span>", b" ", page)
    page = re.sub(b"\\s+", b" ", page)  # tidy up white space

    # capture all links (of ZIP and Microsoft Excel types)
    link_types = (".xlsx", ".zip")  # must be lower case
    soup = BeautifulSoup(page, features="lxml")
    link_dict: dict[str, list[str]] = {}
    for link in soup.findAll("a"):
        url = link.get("href")
        if url is None:
            # ignore silly cases
            continue
        for link_type in link_types:
            if url.lower().endswith(link_type):
                if link_type not in link_dict:
                    link_dict[link_type] = []
                link_dict[link_type].append(_make_absolute_url(url))
                break

    if verbose:
        print("Found links to the following ABS data tables:")
        for link_type, link_list in link_dict.items():
            summary = [_get_table_name(x) for x in link_list]  # just the file name
            print(f"Found: {len(link_list)} items of type {link_type}: {summary}")
        print()

    return link_dict


# private
def _get_meta_from_excel(
    excel: pd.ExcelFile, tab_num: str, tab_desc: str, cat_id: str
) -> pd.DataFrame:
    """Capture the metadata from the Index sheet of an ABS excel file.
    Returns a DataFrame specific to the current excel file.
    Returning an empty DataFrame, mneans that the meatadata could not
    be identified."""

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
            print(f"Could not find metadata for {cat_id}-{tab_num}")
            return pd.DataFrame()

    # make damn sure there are no rogue white spaces
    for col in required:
        file_meta[col] = file_meta[col].str.strip()

    # standarise some units
    file_meta[metacol.unit] = (
        file_meta[metacol.unit]
        .str.replace("000 Hours", "Thousand Hours")
        .replace("$'000,000", "$ Million")
        .replace("$'000", " $ Thousand")
        .replace("000,000", "Millions")
        .replace("000", "Thousands")
    )
    file_meta[metacol.table] = tab_num.strip()
    file_meta[metacol.tdesc] = tab_desc.strip()
    file_meta[metacol.cat] = cat_id.strip()
    return file_meta


# private
def _unpack_excel_into_df(
    excel: pd.ExcelFile, meta: DataFrame, freq: str, verbose: bool
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

        for i in sheet_data.columns:
            if i in data.columns:
                # Remove duplicate Series IDs before merging
                del sheet_data[i]
                continue
            if verbose and sheet_data[i].isna().all():
                # Warn if data series is all NA
                problematic = meta.loc[meta["Series ID"] == i][
                    ["Table", "Data Item Description", "Series Type"]
                ]
                print(f"Warning, this data series is all NA: {i} (details below)")
                print(f"{problematic}\n\n")

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

    return data


# private
def _extract_from_zip(
    zip_contents: bytes, 
    **kwargs: Any,
) -> tuple[dict[str, DataFrame], DataFrame]:
    """Extract the contents of a ZIP file into tuple, where the
    first element is a dictionary of DataFrames; and the second
    element is the ABS meta data in a DataFrame."""

    verbose = kwargs.get("verbose", False)
    if verbose:
        print("Extracting DataFrames from the zip-file.")
    freq_dict = {"annual": "Y", "biannual": "Q", "quarter": "Q", "month": "M"}
    returnable: dict[str, DataFrame] = {}
    meta = DataFrame()

    with zipfile.ZipFile(BytesIO(zip_contents)) as zipped:
        for count, element in enumerate(zipped.infolist()):
            # get the zipfile into pandas
            excel = pd.ExcelFile(BytesIO(zipped.read(element.filename)))

            # get table information (ie. the meta data)
            if "Index" not in excel.sheet_names:
                print(
                    "Caution: Could not find the 'Index' "
                    f"sheet in {element.filename}. File not included"
                )
                continue

            # get table header information
            header = excel.parse("Index", nrows=8)  # ???
            cat_id = header.iat[3, 1].split(" ")[0].strip()
            table_name = _get_table_name(url=element.filename)
            tab_desc = header.iat[4, 1].split(".", 1)[-1].strip()

            # get the metadata rows
            file_meta = _get_meta_from_excel(excel, table_name, tab_desc, cat_id)
            if len(file_meta) == 0:
                continue

            # establish freq - used for making the index a PeriodIndex
            freqlist = file_meta["Freq."].str.lower().unique()
            if not len(freqlist) == 1 or freqlist[0] not in freq_dict:
                print(f"Unrecognised data frequency {freqlist} for {tab_desc}")
                continue
            freq = freq_dict[freqlist[0]]

            # fix tabulation when ABS uses the same table numbers for data
            # This happens occasionally
            if table_name in returnable:
                tmp = f"{table_name}-{count}"
                if verbose:
                    print(f"Changing duplicate table name from {table_name} to {tmp}.")
                table_name = tmp
                file_meta[metacol.table] = table_name

            # aggregate the meta data
            meta = pd.concat([meta, file_meta])

            # add the table to the returnable dictionary
            returnable[table_name] = _unpack_excel_into_df(
                excel, file_meta, freq, verbose
            )

    return returnable, meta


def read_abs_cat(cat: str, **kwargs: Any) -> tuple[dict[str, DataFrame], DataFrame]:
    """Get all the data tables and the metadata for a given ABS catalogue number.
    The data tables are returned as a dictionary of DataFrames, which is
    indexed by the table name. The metadata is returned as a separate 9DataFrame."""

    # convert the catalogue number to the ABS webpage URL
    cm = catalogue_map()
    if cat not in cm.index:
        raise ValueError(f"ABS catalogue number {cat} not found.")
    url = cm.loc[cat, "URL"]

    # get the URL links to the relevant ABS data files on that webpage
    links = get_data_links(url, **kwargs)
    if not links:
        print(f"No data files found for catalogue number {cat}")
        return {}, DataFrame()  # return an empty dictionary, DataFrame

    # read the data files into a dictionary of DataFrames
    abs_data: dict[str, DataFrame] = {}
    abs_meta: DataFrame = DataFrame()

    for link_type in ".zip", ".xlsx":
        for link in links.get(link_type, []):
            if link_type == ".zip":
                zip_contents = get_file(link, **kwargs)
                d, m = _extract_from_zip(zip_contents, **kwargs)
                abs_data.update(d)
                abs_meta = pd.concat([abs_meta, m], axis=0)
            elif link_type == ".xlsx":
                # still to do
                pass

    return abs_data, abs_meta
