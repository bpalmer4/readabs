"""grab_abs_url.py

The ABS produces a lot of products that are not in a 
standard time-series format. This module is designed
to download all of the data tables on a given ABS
webpage, as is, without looking at the format of those 
tables, nor extracting any meta-data. """

# --- imports ---
# standard library imports
import zipfile
from functools import cache
from io import BytesIO
from typing import Any

# analytic imports
import pandas as pd
from pandas import DataFrame

# local imports - ugly, need to find out how to fix this
# print(f"in read_abs_cat.py: __main__={__name__}, __package__={__package__}")
if __package__ is None or __package__ == "":
    from get_data_links import get_data_links, get_table_name
    from read_support import check_kwargs, get_args, HYPHEN
    from download_cache import get_file
    from abs_catalogue_map import catalogue_map
else:
    from .get_data_links import get_data_links, get_table_name
    from .read_support import check_kwargs, get_args, HYPHEN
    from .download_cache import get_file
    from .abs_catalogue_map import catalogue_map


# --- public - primary entry point for this module
@cache  # minimise slowness with repeat business
def grab_abs_url(
    url: str = None,  # ABS catalogue number
    **kwargs: Any,  # keyword arguments
) -> dict[str, DataFrame]:
    """Identify and load Excel/zip data found on a webpage given by an
    ABS landing page URL for an ABS Catalogue item. For example, the URL
    for the ABS weekly jobs payroll data is:
    https://www.abs.gov.au/statistics/labour/jobs/weekly-payroll-jobs/latest-release

    Parameters
    ----------
    url : str
        A URL for an ABS Catalogue landing page.
    **kwargs : Any
        Keyword arguments for the read_abs_cat function.

    Returns
    -------
    A dictionary of DataFrames extracted from the webpage. These
    will include data dataframes, as well as any explanatory
    material that is found in an Excel file, that has been stuffed
    (perhaps haphazardly) into a DataFrame. Note: dates and numbers
    may be encoded as strings."""

    # check/get the keyword arguments
    url = _get_url(url, kwargs)  # removes "cat" from kwargs
    check_kwargs(kwargs, "grab_abs_url")
    args = get_args(kwargs, "grab_abs_url")

    # get the URL links to the relevant ABS data files on that webpage
    links = get_data_links(url, **args)
    if not links:
        print(f"No data files found at URL: {url}")
        return DataFrame()  # return an empty DataFrame

    # read the data files into a dictionary of DataFrames
    abs_dict: dict[str, DataFrame] = {}

    def find(targ_type: str, target: str) -> str:
        """Find the URL for a target file type."""
        targ_list = links.get(targ_type, [])
        if not targ_list:
            return ""
        for link in targ_list:
            name = get_table_name(link)
            if name == target:
                return link
        return ""

    # use the args, and the found links to get the data ...
    if args["single_excel_only"]:
        link = find(".xlsx", args["single_excel_only"])
        if link:
            abs_dict = _add_excel(abs_dict, link, **args)

    elif args["single_zip_only"]:
        link = find(".zip", args["single_zip_only"])
        if link:
            abs_dict = _add_zip(abs_dict, link, **args)

    else:
        for link_type in ".zip", ".xlsx":  # .zip must come first
            for link in links.get(link_type, []):

                if link_type == ".zip" and args["get_zip"]:
                    abs_dict = _add_zip(abs_dict, link, **args)

                elif link_type == ".xlsx":
                    if (
                        args["get_excel"]
                        or (args["get_excel_if_no_zip"] and not args["get_zip"])
                        or (args["get_excel_if_no_zip"] and not links.get(".zip", []))
                    ):
                        abs_dict = _add_excel(abs_dict, link, **args)

    return abs_dict


# --- private
def _get_url(url: str, kwargs: dict) -> str:
    """If an ABS 'cat' is provided, get the URL for the ABS data
    files on the ABS webpage. Otherwise, return the URL provided.
    Either the 'url' or 'cat' argument must be provided."""

    cat = kwargs.pop("cat", None)
    cm = catalogue_map()
    if cat is not None and cat in cm.index:
        url = cm.loc[cat, "URL"]
    if url is None and cat is None:
        raise ValueError("_grab_abs_url(): no URL or Catalogue number provided.")

    return url


def _add_zip(abs_dict: dict[str, DataFrame], link: str, **args) -> dict[str, DataFrame]:
    """Read in the zip-zip file at the URL in the 'link' argument.
    Iterate over the contents of that zip-file, calling
    _add_excel_bytes() to put those contents into the dictionary of
    DataFrames given by 'abs_dict'. When done, return the dictionary
    of DataFrames."""

    zip_contents = get_file(link, **args)
    if len(zip_contents) == 0:
        return abs_dict

    with zipfile.ZipFile(BytesIO(zip_contents)) as zipped:
        for element in zipped.infolist():

            # get the zipfile into pandas
            table_name = get_table_name(url=element.filename)
            raw_bytes = zipped.read(element.filename)
            abs_dict = _add_excel_bytes(abs_dict, raw_bytes, table_name, args)

    return abs_dict


def _add_excel_bytes(
    abs_dict: dict[str, DataFrame],
    raw_bytes: bytes,
    name: str,
    args: Any,
) -> dict[str, DataFrame]:
    """Assume the bytes at 'raw_bytes' represemt an Excel file.
    Convert each sheet in the Excel file to a DataFrame, and place
    those DataFrames in the dictionary of DataFrames given by
    'abs_dict', using 'name---sheet_name' as a key.
    When done, return the dictionary of DataFrames."""

    ignore_errors = args.get("ignore_errors", False)
    verbose = args.get("verbose", False)

    if len(raw_bytes) == 0:
        if verbose:
            print("_add_excel_bytes(): the raw bytes are empty.")
        return abs_dict

    # convert the raw bytes into a pandas ExcelFile
    try:
        excel = pd.ExcelFile(BytesIO(raw_bytes))
    except Exception as e:
        message = f"With {name}: could not convert raw bytes to ExcelFile.\n{e}"
        if ignore_errors:
            print(message)
            return abs_dict
        raise RuntimeError(message) from e
    excel = pd.ExcelFile(BytesIO(raw_bytes))

    # iterate over the sheets in the Excel file
    for sheet_name in excel.sheet_names:
        # grab and go - no treatment of the data
        sheet_data = excel.parse(
            sheet_name,
        )
        if len(sheet_data) == 0:
            if verbose:
                print(f"_add_excel_bytes(): sheet {sheet_name} in {name} is empty.")
            continue
        abs_dict[f"{name}{HYPHEN}{sheet_name}"] = sheet_data

    # return the dictionary of DataFrames
    return abs_dict


def _add_excel(
    abs_dict: dict[str, DataFrame],
    link: str,
    **args: Any,
) -> tuple[dict[str, DataFrame], DataFrame]:
    """Read in an Excel file at the URL in the 'link' argument.
    Pass those bytes to _add_excel_bytes() to put the contents
    into the dictionary of DataFrames given by 'abs_dict'. When done,
    return the dictionary of DataFrames."""

    name = get_table_name(link)

    if name in abs_dict:
        # table already in the dictionary
        return abs_dict

    raw_bytes = get_file(link, **args)

    abs_dict = _add_excel_bytes(abs_dict, raw_bytes, name, args)

    return abs_dict


# --- main ---
if __name__ == "__main__":
    # briefly test this module

    # grab a single Excel file
    test_dict = grab_abs_url(cat="6202.0", get_excel=True, single_excel_only="6202001")
    print(test_dict.keys())
    print(f"Done.\n{'=' * 20}\n")

    # grab the whole shebang
    urls = [
        "https://www.abs.gov.au/statistics/labour/jobs/"
        + "weekly-payroll-jobs/latest-release",
        "https://www.abs.gov.au/statistics/people/population/"
        + "national-state-and-territory-population/dec-2023",
    ]
    for url_ in urls:
        print(f"Grabbing data from: {url_}")
        data_dict = grab_abs_url(url_, verbose=True)
        print(data_dict.keys())
        print(f"Done.\n{'=' * 20}\n")
