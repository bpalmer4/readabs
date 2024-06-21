"""Download and package timeseries data from the
Australian Bureau of Statistics (ABS)."""

# --- imports ---
# standard library imports
import re
from functools import cache

# analytic imports
import pandas as pd
from bs4 import BeautifulSoup

# local imports
from catalogue_map import catalogue_map
from get_url_cache import get_file, HttpError, CacheError


# --- functions ---
# private
def _make_absolute_url(url: str, ) -> str:
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
        page = get_file(url)
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
