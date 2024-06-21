"""Download timeseries data from the
Australian Bureau of Statistics (ABS)
and package that data into DataFrames."""

# --- imports ---
# standard library imports
import re
import zipfile
from functools import cache
from io import BytesIO
from typing import Any

# analytic imports
import pandas as pd
from pandas import DataFrame
from bs4 import BeautifulSoup

# local imports
from abs_meta_data_support import metacol
from catalogue_map import catalogue_map
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


# public
@cache
def get_data_links(
    url: str,
    verbose: bool = False,
    inspect_file_name="",  # for debugging - save the page to disk
    **kwargs,
) -> dict[str, list[str]]:
    """Scan the ABS URL for links to ZIP files and for
    links to Microsoft Excel files. Return the links in
    a dictionary of lists by file type ending. Ensure relative
    links are fully expanded."""

    # get relevant web-page from ABS website
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

    # capture all links (of the ZIP and Microsoft Excel types)
    link_types = (".xlsx", ".zip", ".xls")  # must be lower case
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
        for link_type, link_list in link_dict.items():
            summary = [x.split("/")[-1] for x in link_list]  # just the file name
            print(f"Found: {len(link_list)} items of type {link_type}: {summary}")

    return link_dict


# private
def _get_table_name(url: str) -> str:
    """Get the table name from the ABS URL."""

    tail = url.rsplit("/", 1)[-1]
    table_name = tail.split(".")[0]
    return table_name


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
            excel = pd.ExcelFile(io.BytesIO(zipped.read(element.filename)))

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

    returnable[META_DATA] = meta
    return returnable


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
                pass

    return abs_data, abs_meta
