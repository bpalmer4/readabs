"""Catalogue map for ABS data."""

from functools import cache
from io import StringIO
from pandas import DataFrame, Series, Index, read_html
from readabs.download_cache import get_file


@cache
def abs_catalogue(cache_only=False, verbose=False) -> DataFrame:
    """Return a DataFrame of ABS Catalogue numbers. In the first instance,
    this is downloaded from the ABS website, and cached for future use.

    Parameters
    ----------
    cache_only : bool = False
        If True, only use the cache.
    verbose : bool = False
        If True, print progress messages.

    Returns
    -------
    DataFrame
        A DataFrame of ABS Catalogue numbers.

    Example
    -------
    ```python
    import readabs as ra
    catalogue = ra.abs_catalogue()
    ```"""

    # get ABS web page of catalogue numbers
    url = "https://www.abs.gov.au/about/data-services/help/abs-time-series-directory"
    abs_bytes = get_file(url, cache_only=cache_only, verbose=verbose)
    links = read_html(StringIO(abs_bytes.decode("utf-8")), extract_links="body")[
        1
    ]  # second table on the page

    # extract catalogue numbers
    cats = links["Catalogue Number"].apply(Series)[0]
    urls = links["Topic"].apply(Series)[1]
    root = "https://www.abs.gov.au/statistics/"
    snip = urls.str.replace(root, "")
    snip = (
        snip[~snip.str.contains("http")].str.replace("-", " ").str.title()
    )  # remove bad cases
    frame = snip.str.split("/", expand=True).iloc[:, :3]
    frame.columns = Index(["Theme", "Parent Topic", "Topic"])
    frame["URL"] = urls
    cats = cats[frame.index]
    cat_index = cats.str.replace("(Ceased)", "").str.strip()
    status = Series(" ", index=cats.index).where(cat_index == cats, "Ceased")
    frame["Status"] = status
    frame.index = Index(cat_index)
    frame.index.name = "Catalogue ID"
    return frame


if __name__ == "__main__":
    print(abs_catalogue())
