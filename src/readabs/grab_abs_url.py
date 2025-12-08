"""Find and extract DataFrames from an ABS webpage."""

# --- imports ---
# standard library imports
import zipfile
from functools import cache
from io import BytesIO
from pathlib import Path
from typing import Any, Unpack

# analytic imports
import pandas as pd
from pandas import DataFrame

from readabs.abs_catalogue import abs_catalogue
from readabs.download_cache import get_file

# local imports
from readabs.get_abs_links import get_abs_links, get_table_name
from readabs.read_support import HYPHEN, ReadArgs, check_kwargs, get_args

# --- constants ---
# File extensions for ABS data files
ZIP_EXTENSION = ".zip"
EXCEL_EXTENSION = ".xlsx"

# Processing order: ZIP files must be processed before Excel files
# This prevents duplicate data when ZIP files contain Excel files
FILE_EXTENSIONS_PROCESSING_ORDER = (ZIP_EXTENSION, EXCEL_EXTENSION)

# Default values and limits
EMPTY_BYTES_LENGTH = 0


# --- public - primary entry point for this module
@cache  # minimise slowness with repeat business
def grab_abs_url(
    cat: str = "",
    url: str = "",
    **kwargs: Unpack[ReadArgs],
) -> dict[str, DataFrame]:
    """For a given URL, extract the data from the Excel and ZIP file links found on that page.

    The data is returned as a dictionary of DataFrames. The Excel files are converted
    into DataFrames, with each sheet in each Excel file becoming a separate DataFrame.
    ZIP files are examined for Excel files, which are similarly converted into
    DataFrames. The dictionary of DataFrames is returned.

    The preferred mechanism for reading ABS data is to use the `read_abs_cat()`
    or `read_abs_series()` functions. This function is provided for those
    cases where the data is not available in the ABS catalogue, where the
    data is not a timeseries, or where the user wants to extract data from
    a specific ABS landingpage.


    Parameters
    ----------
    url : str = ""
        A URL for an ABS Catalogue landing page. Either a url or
        a catalogue number must be provided. If both are provided, the
        URL will be used.

    cat : str = ""
        An ABS Catalogue number. If provided, and the URL is not
        provided, then the Catalogue number will be used to get the URL.

    **kwargs : Unpack[ReadArgs]
        Accepts the same keyword arguments as `read_abs_cat()`.

    Returns
    -------
    dict[str, DataFrame]
        A dictionary of DataFrames.

    """
    # check/get the keyword arguments
    url = _get_url(url, cat)
    check_kwargs(kwargs, "grab_abs_url")  # warn if invalid kwargs
    args = get_args(kwargs, "grab_abs_url")  # get the valid kwargs
    if verbose := args["verbose"]:
        print(f"grab_abs_url(): {url=}, {args=}")

    # get the URL links to the relevant ABS data files on that webpage
    links = get_abs_links(url, **args)
    if not links:
        print(f"No data files found at URL: {url}")
        return {}  # return an empty Dictionary

    # read the data files into a dictionary of DataFrames
    abs_dict: dict[str, DataFrame] = {}

    # Process single file requests first
    abs_dict = _process_single_files(abs_dict, links, args, verbose=verbose)
    if abs_dict:  # If single file was found and processed, return it
        return abs_dict

    # Process all files based on configuration
    return _process_all_files(abs_dict, links, args)


def grab_abs_zip(
    zip_path: Path | str,
    **kwargs: Unpack[ReadArgs]
) -> dict[str, DataFrame]:
    """Grab and process a single ABS ZIP file from a file system location.

    This is a convenience function that opens an ABS ZIP file from a local
    filesystem path. Expect to be used rarely.

    Parameters
    ----------
    zip_path : Path | str
        The local filesystem path of the ABS ZIP file to open and process.

    **kwargs : Unpack[ReadArgs]
        Additional keyword arguments for file retrieval and processing.

    Returns
    -------
    dict[str, DataFrame]
        A dictionary of DataFrames extracted from the ZIP file.

    """
    check_kwargs(kwargs, "grab_abs_zip")  # warn if invalid kwargs
    args = get_args(kwargs, "grab_abs_zip")  # get the valid kwargs

    zp: Path = zip_path if isinstance(zip_path, Path) else Path(zip_path)
    zip_bytes = zp.read_bytes()
    abs_dict: dict[str, DataFrame] = {}
    return _process_zip(abs_dict, zip_bytes, **args)


# --- private
def _process_single_files(
    abs_dict: dict[str, DataFrame],
    links: dict[str, list[str]],
    args: dict[str, Any],  # ReadArgs after processing
    *,
    verbose: bool,
) -> dict[str, DataFrame]:
    """Process single file requests (single_excel_only or single_zip_only)."""
    if args["single_excel_only"]:
        link = _find_url(links, EXCEL_EXTENSION, args["single_excel_only"], verbose=verbose)
        if link:
            return _add_excel(abs_dict, link, **args)

    if args["single_zip_only"]:
        link = _find_url(links, ZIP_EXTENSION, args["single_zip_only"], verbose=verbose)
        if link:
            return _add_zip(abs_dict, link, **args)

    return abs_dict


def _process_all_files(
    abs_dict: dict[str, DataFrame],
    links: dict[str, list[str]],
    args: dict[str, Any],  # ReadArgs after processing
) -> dict[str, DataFrame]:
    """Process all files based on configuration (get_zip, get_excel, etc.)."""
    for link_type in FILE_EXTENSIONS_PROCESSING_ORDER:
        for link in links.get(link_type, []):
            if link_type == ZIP_EXTENSION and args["get_zip"]:
                abs_dict = _add_zip(abs_dict, link, **args)
            elif link_type == EXCEL_EXTENSION and _should_process_excel_file(args, links):
                abs_dict = _add_excel(abs_dict, link, **args)
    return abs_dict


def _should_process_excel_file(args: dict[str, Any], links: dict[str, list[str]]) -> bool:
    """Determine if Excel files should be processed based on configuration.

    Excel files are processed if:
    1. get_excel is explicitly True, or
    2. get_excel_if_no_zip is True AND (get_zip is False OR no ZIP files are available)

    Args:
        args: Configuration arguments from user
        links: Dictionary of available file links by type

    Returns:
        bool: True if Excel files should be processed

    """
    # Always process if explicitly requested
    if args["get_excel"]:
        return True

    # Process Excel if requested when no ZIP files, and either:
    # - ZIP processing is disabled, or
    # - No ZIP files are available
    if args["get_excel_if_no_zip"]:
        zip_processing_disabled = not args["get_zip"]
        no_zip_files_available = not links.get(ZIP_EXTENSION, [])
        return zip_processing_disabled or no_zip_files_available

    return False


def _find_url(links: dict[str, list[str]], targ_type: str, target: str, *, verbose: bool = False) -> str:
    """Find the URL for a target file type.

    Args:
        links: Dictionary mapping file types to lists of URLs
        targ_type: Target file extension (e.g., '.xlsx', '.zip')
        target: Target filename without extension
        verbose: Whether to print debug information

    Returns:
        str: The matching URL if found, otherwise an empty string

    """
    targ_list = links.get(targ_type, [])
    if not targ_list:
        return ""
    goal = f"{target}{targ_type}"
    if verbose:
        print(f"_find_url(): looking for {goal} in {targ_list}.")
    for link in targ_list:
        if link.endswith(goal):
            return link
    return ""


def _get_url(url: str, cat: str) -> str:
    """Get URL from provided URL or catalogue number.

    If an ABS catalogue number is provided and URL is not provided,
    get the URL for the ABS data files on the ABS webpage.
    Otherwise, return the URL provided. Either the 'url' or
    'cat' argument must be provided.

    Args:
        url: The URL to use if provided
        cat: The catalogue number to use if URL is not provided

    Returns:
        str: The URL to use for data retrieval

    Raises:
        ValueError: If neither URL nor valid catalogue number is provided

    """
    if not url and cat:
        try:
            cat_map = abs_catalogue()
            if cat in cat_map.index:
                url = str(cat_map.loc[cat, "URL"])
        except (KeyError, IndexError) as e:
            raise ValueError(f"Catalogue number '{cat}' not found in ABS catalogue: {e}") from e
        except (ConnectionError, TimeoutError) as e:
            raise ValueError(f"Network error retrieving catalogue for '{cat}': {e}") from e
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid catalogue data for '{cat}': {e}") from e

    if not url and cat:
        raise ValueError(
            f"Catalogue number '{cat}' not found in the ABS Time Series Directory. "
            f"This may be a discontinued series. If you know the ABS landing page URL, "
            f"you can use: read_abs_cat(cat='{cat}', url='https://www.abs.gov.au/...')"
        )

    if not url:
        raise ValueError("_get_url(): no URL or valid catalogue number provided.")

    return url


def _process_zip(
    abs_dict: dict[str, DataFrame],
    zip_contents: bytes,
    **args: Any,  # ReadArgs compatible
) -> dict[str, DataFrame]:
    """Read and process a ZIP file's contents from bytes."""
    if len(zip_contents) == EMPTY_BYTES_LENGTH:
        return abs_dict

    with zipfile.ZipFile(BytesIO(zip_contents)) as zipped:
        for element in zipped.infolist():
            # get the zipfile into pandas
            table_name = get_table_name(url=element.filename)
            raw_bytes = zipped.read(element.filename)
            abs_dict = _add_excel_bytes(abs_dict, raw_bytes, table_name, args)

    return abs_dict


def _add_zip(
    abs_dict: dict[str, DataFrame],
    link: str,
    **args: Any,  # ReadArgs compatible
) -> dict[str, DataFrame]:
    """Read and process a ZIP file from a URL.

    Downloads the ZIP file and iterates over its contents, calling
    _add_excel_bytes() to extract Excel files and add their contents
    to the DataFrames dictionary.

    Args:
        abs_dict: Dictionary to store extracted DataFrames
        link: URL to the ZIP file
        **args: Additional arguments passed to file retrieval functions

    Returns:
        dict[str, DataFrame]: Updated dictionary with new DataFrames from ZIP contents

    """
    zip_contents = get_file(link, **args)
    return _process_zip(abs_dict, zip_contents, **args)


def _add_excel_bytes(
    abs_dict: dict[str, DataFrame],
    raw_bytes: bytes,
    name: str,
    args: dict[str, Any],  # ReadArgs after processing
) -> dict[str, DataFrame]:
    """Convert Excel file bytes to DataFrames and add to dictionary.

    Processes the bytes as an Excel file, converting each sheet to a DataFrame
    and adding them to the dictionary using 'name---sheet_name' as keys.

    Args:
        abs_dict: Dictionary to store extracted DataFrames
        raw_bytes: Bytes content of the Excel file
        name: Base name for the Excel file
        args: Dictionary of processing arguments

    Returns:
        dict[str, DataFrame]: Updated dictionary with new DataFrames from Excel sheets

    """
    verbose = args.get("verbose", False)

    if len(raw_bytes) == EMPTY_BYTES_LENGTH:
        if verbose:
            print("_add_excel_bytes(): the raw bytes are empty.")
        return abs_dict

    # convert the raw bytes into a pandas ExcelFile
    try:
        excel = pd.ExcelFile(BytesIO(raw_bytes))
    except (ValueError, TypeError) as e:
        message = f"With {name}: could not convert raw bytes to ExcelFile.\n{e}"
        print(message)
        return abs_dict

    # iterate over the sheets in the Excel file
    for sheet_name in excel.sheet_names:
        # grab and go - no treatment of the data
        sheet_data = excel.parse(
            sheet_name,
        )
        if len(sheet_data) == EMPTY_BYTES_LENGTH:
            if verbose:
                print(f"_add_excel_bytes(): sheet {sheet_name} in {name} is empty.")
            continue
        abs_dict[f"{name}{HYPHEN}{sheet_name}"] = sheet_data

    # return the dictionary of DataFrames
    return abs_dict


def _add_excel(
    abs_dict: dict[str, DataFrame],
    link: str,
    **args: Any,  # ReadArgs compatible
) -> dict[str, DataFrame]:
    """Read in an Excel file at the URL in the 'link' argument.

    Pass those bytes to _add_excel_bytes() to put the contents
    into the dictionary of DataFrames given by 'abs_dict'. When done,
    return the dictionary of DataFrames.
    """
    name = get_table_name(link)

    if name in abs_dict:
        # table already in the dictionary
        return abs_dict

    raw_bytes = get_file(link, **args)

    return _add_excel_bytes(abs_dict, raw_bytes, name, args)


# --- main ---
if __name__ == "__main__":

    def simple_test() -> None:
        """Test the grab_abs_url and grab_abs_zip functions."""

        def test(name: str, **kwargs: Any) -> None:  # ReadArgs compatible
            print(f"TEST -- {name}")
            try:
                data_dict = grab_abs_url(**kwargs)
                print("---")
                if not data_dict:
                    print("PROBLEM -- No data found.")
                else:
                    print(f"SUCCESS -- Found {len(data_dict)} datasets: {list(data_dict.keys())}")
            except Exception as e:  # pylint: disable=broad-except
                print(f"ERROR -- Test failed with exception: {e}")
            print(f"Done.\n{'=' * 20}\n")

        def test_zip(zip_path: Path, **kwargs: Any) -> None:  # ReadArgs compatible
            print(f"TEST -- grab_abs_zip() with {zip_path}")
            try:
                data_dict = grab_abs_zip(zip_path, **kwargs)
                print("---")
                if not data_dict:
                    print("PROBLEM -- No data found.")
                else:
                    print(f"SUCCESS -- Found {len(data_dict)} datasets: {list(data_dict.keys())}")
            except Exception as e:  # pylint: disable=broad-except
                print(f"ERROR -- Test failed with exception: {e}")
            print(f"Done.\n{'=' * 20}\n")

        # 4 -- grab from url
        _name = ".test-data/Qrtly-CPI-Time-series-spreadsheets-all.zip"
        _zip_path = Path(_name)
        test_zip(_zip_path, verbose=True)

        # --- various grab_abs_url() tests

        name = "1 -- grab a single zip file"
        test(
            name,
            cat="6291.0.55.001",
            single_zip_only="p6291_all_quarterly_spreadsheets",
            get_zip=True,
            verbose=True,
        )

        name = "2 -- grab a single Excel file"
        test(
            name,
            cat="6202.0",
            get_excel=True,
            single_excel_only="6202001",
            verbose=False,
        )

        # 3 -- grab the whole shebang
        urls = [
            "https://www.abs.gov.au/statistics/labour/jobs/weekly-payroll-jobs/latest-release",
            "https://www.abs.gov.au/statistics/people/population/national-state-and-territory-population/dec-2023",
        ]
        for i, url_ in enumerate(urls):
            name = f"3.{i} -- grab the whole shebang {url_}"
            test(name, url=url_, verbose=True)

    simple_test()
