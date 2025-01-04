"""Extract links to RBA data files from the RBA website."""

# system imports
import re
from typing import Any
from functools import cache

# analutic imports
from bs4 import BeautifulSoup
from pandas import DataFrame

# local imports
from readabs.download_cache import get_file, HttpError, CacheError


# --- public functions ---
@cache
def rba_catalogue(cache_only=False, verbose=False) -> DataFrame:
    """Return a DataFrame of RBA Catalogue numbers. In the first instance,
    this is downloaded from the RBA website, and cached for future use.

    Parameters
    ----------
    cache_only : bool = False
        If True, only use the cache.
    verbose : bool = False
        If True, print progress messages.

    Returns
    -------
    DataFrame
        A DataFrame of RBA Catalogue numbers.

    Example
    -------
    ```python
    import readabs as ra
    catalogue = ra.rba_catalogue()
    ```"""

    return _get_rba_links(cache_only=cache_only, verbose=verbose)


def print_rba_catalogue(cache_only=False, verbose=False) -> None:
    """This function prints to standard output a table of the RBA
    Catalogue Numbers.

    Parameters
    ----------
    cache_only : bool = False
        If True, only use the cache.
    verbose : bool = False
        If True, print progress messages.

    Return values
    -------------

    The function does not return anything.

    Example
    -------

    ```python
    import readabs as ra
    ra.print_rba_catalogue()
    ```"""

    rba_catalog = rba_catalogue(cache_only=cache_only, verbose=verbose)
    print(rba_catalog.loc[:, rba_catalog.columns != "URL"].to_markdown())


# --- private functions ---
def _get_soup(url: str, **kwargs: Any) -> BeautifulSoup | None:
    """Return a BeautifulSoup object from a URL.
    Returns None on error."""

    try:
        page = get_file(url, **kwargs)
    except (HttpError, CacheError) as e:
        print(f"Error: {e}")
        return None

    # remove those pesky span tags - possibly not necessary
    page = re.sub(b"<span[^>]*>", b" ", page)
    page = re.sub(b"</span>", b" ", page)
    page = re.sub(b"\\s+", b" ", page)  # tidy up white space

    return BeautifulSoup(page, "html.parser")


def _historical_name_fix(
    moniker: str,
    foretext: str,
    prefix: str,
) -> tuple[str, str]:
    """Fix the historical data names. Returns a tuple of moniker and foretext."""

    if "Exchange Rates" in foretext:
        foretext = f"{foretext} - {moniker}"
        moniker = "F11.1"

    for word in ["Daily", "Monthly", "Detailed", "Summary", "Allotted"]:
        if word in foretext:
            moniker = f"{moniker}-{word}"
            break

    last = foretext.rsplit(" ", 1)[-1]
    if re.match(r"\d{4}", last):
        moniker = f"{moniker}-{last}"

    moniker = f"{prefix}{moniker}"

    return moniker, foretext


def _excel_link_capture(
    soup: BeautifulSoup,
    prefix: str,
) -> dict[str, dict[str, str]]:
    """Capture all links (of Microsoft Excel types) from the
    BeautifulSoup object. Returns a dictionary with the following
    structure: {moniker: {"Description": text, "URL": url}}."""

    # The RBA has a number of historic tables that are not well
    # formated. We will exclude these from the dictionary.
    historic_exclusions = ("E4", "E5", "E6", "E7", "J1", "J2")

    link_dict = {}
    for link in soup.findAll("a"):

        url = link.get("href").strip()
        if not url or url is None:
            continue

        tail = url.rsplit("/", 1)[-1].lower()
        if "." not in tail:
            continue
        if not tail.endswith(".xls") and not tail.endswith(".xlsx"):
            continue
        text, url = link.text, _make_absolute_url(url.strip())
        text = text.replace("–", "-").strip()

        pair = text.rsplit(" - ", 1)
        if len(pair) != 2:
            continue
        foretext, moniker = pair

        if prefix:
            # Remove historical data that does not easily
            # parse under the same rules as for the current data.
            if moniker in historic_exclusions:
                continue
            if "Occasional Paper" in moniker:
                continue

            # The historical data is a bit ugly. Let's clean it up.
            moniker, foretext = _historical_name_fix(moniker, foretext, prefix)

        if moniker in link_dict:
            print(f"Warning: {moniker} already exists in the dictionary {tail}")
            if tail != ".xlsx":
                # do not replace a .xlsx link with an .xls link
                continue
        link_dict[moniker] = {"Description": foretext.strip(), "URL": url}

    return link_dict


@cache
def _get_rba_links(**kwargs: Any) -> DataFrame:
    """Extract links to RBA data files in Excel format
    from the RBA website.  Returns a DataFrame with the
    following columns: 'Description' and 'URL'. The index
    is the 'Table' number. Returns an empty DataFrame on error."""

    urls = [
        # (url, prefix)
        ("https://www.rba.gov.au/statistics/tables/", ""),  # current
        ("https://www.rba.gov.au/statistics/historical-data.html", "Z:"),  # history
    ]

    link_dict = {}
    for url, prefix in urls:
        soup = _get_soup(url, **kwargs)
        if soup is not None:
            link_dict.update(_excel_link_capture(soup, prefix))

    rba_catalog = DataFrame(link_dict).T.sort_index()
    rba_catalog.index.name = "Table"
    return rba_catalog


# private
def _make_absolute_url(url: str, prefix: str = "https://www.rba.gov.au") -> str:
    """Convert a relative URL address found on the RBA site to
    an absolute URL address."""

    # remove a prefix if it already exists (just to be sure)
    url = url.replace(prefix, "")
    url = url.replace(prefix.replace("https://", "http://"), "")
    # then add the prefix (back) ...
    return f"{prefix}{url}"


# --- testing ---
if __name__ == "__main__":
    print_rba_catalogue(cache_only=False, verbose=False)
