"""get_rba_links.py: Extract links to RBA data files from the RBA website."""

# system imports
import re
from typing import Any
from bs4 import BeautifulSoup
from functools import cache

# analutic imports
from pandas import DataFrame

# local imports
# multiple imports to allow for direct testing before packaging
try:
    from .download_cache import get_file, HttpError, CacheError
except ImportError:
    from download_cache import get_file, HttpError, CacheError


# --- public functions ---
@cache
def get_rba_links(**kwargs: Any) -> DataFrame:
    """Extract links to RBA data files in Excel format
    from the RBA website."""

    verbose = kwargs.get("verbose", False)
    cache_only = kwargs.get("cache_only", False)
    print(f"{cache_only=} {verbose=}")
    urls = ("https://www.rba.gov.au/statistics/tables/",)
    link_dict = {}
    for url in urls:
        try:
            page = get_file(url, **kwargs)
        except HttpError as e:
            print(f"Error: {e}")
            return link_dict
        except CacheError as e:
            print(f"Error: {e}")
            return link_dict

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
            link_dict[moniker] = {"Description": foretext.strip(), "URL": url}
    rba_catalog = DataFrame(link_dict).T.sort_index()
    rba_catalog.index.name = "Table"
    return rba_catalog


@cache
def rba_catalogue(cache_only=False, verbose=False) -> DataFrame:
    """Return a DataFrame of RBA data file links."""

    return get_rba_links(cache_only=cache_only, verbose=verbose)


def print_rba_catalogue(cache_only=False, verbose=False) -> None:
    """Print the RBA data file links."""

    rba_catalog = rba_catalogue(cache_only=cache_only, verbose=verbose)
    print(rba_catalog.loc[:, rba_catalog.columns != "URL"].to_markdown())


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
    print_rba_catalogue(cache_only=True, verbose=True)
