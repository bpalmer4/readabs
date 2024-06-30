"""For a specified Catalogue number, download from the ABS 
website the links for the zip files and the Microsoft Excel 
files that contain the data tables."""

import re
from typing import Any
from bs4 import BeautifulSoup

# local imports - ugly, need to find out how to fix thiscd
if __package__ is None or __package__ == "":
    from download_cache import get_file, HttpError, CacheError
else:
    from .download_cache import get_file, HttpError, CacheError


# private
def _make_absolute_url(url: str, prefix: str = "https://www.abs.gov.au") -> str:
    """Convert a relative URL address found on the ABS site to
    an absolute URL address."""

    # remove a prefix if it already exists (just to be sure)
    url = url.replace(prefix, "")
    url = url.replace(prefix.replace("https://", "http://"), "")
    # then add the prefix (back) ...
    return f"{prefix}{url}"


# public (also used by read_abs_cat.py)
def get_table_name(url: str) -> str:
    """Get the table name from the ABS URL."""

    tail = url.rsplit("/", 1)[-1]
    table_name = tail.split(".")[0]
    return table_name


# private
def historicise_links(
    link_dict: dict[str, list[str]], history: str
) -> dict[str, list[str]]:
    """Age an ABS link so that it points to a historical version of the data.
    Note: the history string is typically in "mon-yr" format, but not alwayts.
    Note: we are also assuming that the date is in the second last part of the URL.
    These assumptions may not always hold."""

    new_dict = {}
    for link_type, link_list in link_dict.items():
        new_list = []
        for link in link_list:
            head, _, tail = link.rsplit("/", 2)
            replacement = "/".join([head, history, tail])
            new_list.append(replacement)
        new_dict[link_type] = new_list

    return new_dict


# public
def get_data_links(
    url: str,  # the URL of the ABS page to scan
    inspect_file_name="",  # for debugging - save the page to disk
    **kwargs: Any,
) -> dict[str, list[str]]:
    """Scan the webpage at the ABS URL for links to ZIP files and for
    links to Microsoft Excel files.
    Return the links in a dictionary of lists undexed by file type ending.
    Ensure relative links have been fully expanded to be absolute links."""

    # get relevant web-page from ABS website
    verbose = kwargs.get("verbose", False)
    if verbose:
        print("Getting data links from the ABS web page.")
    try:
        page = get_file(url, **kwargs)
    except (HttpError, CacheError) as e:
        print(f"Error when obtaining links from ABS web page: {e}")
        return {}

    # save the HTML webpage to disk for inspection
    if inspect_file_name:
        with open(inspect_file_name, "w", encoding="utf-8") as file_handle:
            file_handle.write(page.decode("utf-8"))

    # remove those pesky span tags - probably not necessary
    page = re.sub(b"<span[^>]*>", b" ", page)
    page = re.sub(b"</span>", b" ", page)
    page = re.sub(b"\\s+", b" ", page)  # tidy up white space

    # capture all links (of ZIP and Microsoft Excel types)
    link_types = (
        ".zip",
        ".xlsx",
    )  # must be lower case
    soup = BeautifulSoup(page, features="lxml")
    link_dict: dict[str, list[str]] = {}
    for link in soup.findAll("a"):
        url = link.get("href")
        if url is None:
            # ignore silly cases
            continue
        if "pivot" in url.rsplit("/", 1)[-1].lower():
            # ignore pivot tables
            continue
        for link_type in link_types:
            if url.lower().endswith(link_type):
                if link_type not in link_dict:
                    link_dict[link_type] = []
                link_dict[link_type].append(_make_absolute_url(url))
                break

    # age links if required
    history = kwargs.get("history", "")
    if history:
        link_dict = historicise_links(link_dict, history)

    if verbose:
        print("Found links to the following ABS data tables:")
        for link_type, link_list in link_dict.items():
            summary = [get_table_name(x) for x in link_list]  # just the file name
            print(f"Found: {len(link_list)} items of type {link_type}: {summary}")
        print()

    return link_dict
