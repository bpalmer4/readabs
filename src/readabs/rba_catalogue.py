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
@cache
def _get_rba_links(**kwargs: Any) -> DataFrame:
    """Extract links to RBA data files in Excel format
    from the RBA website.  Returns a DataFrame with the
    following columns: 'Description' and 'URL'. The index
    is the 'Table' number. Returns an empty DataFrame on error."""

    verbose = kwargs.get("verbose", False)
    urls = ("https://www.rba.gov.au/statistics/tables/",)
    link_dict = {}
    for url in urls:
        try:
            page = get_file(url, **kwargs)
        except HttpError as e:
            print(f"Error: {e}")
            return DataFrame()
        except CacheError as e:
            print(f"Error: {e}")
            return DataFrame()

        # remove those pesky span tags - probably not necessary
        page = re.sub(b"<span[^>]*>", b" ", page)
        page = re.sub(b"</span>", b" ", page)
        page = re.sub(b"\\s+", b" ", page)  # tidy up white space

        # parse the HTML content
        soup = BeautifulSoup(page, "html.parser")

        # capture all links (of Microsoft Excel types)
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

            spudle = text.rsplit(" - ", 1)
            if len(spudle) != 2:
                if verbose:
                    print(f"Note: {text} - {url} did not split into two parts?")
                continue
            foretext, moniker = spudle

            if moniker in link_dict:
                print(f"Warning: {moniker} already exists in the dictionary {tail}")
                if tail != ".xlsx":
                    # do not replace a .xlsx link with an .xls link
                    continue
            link_dict[moniker] = {"Description": foretext.strip(), "URL": url}
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
