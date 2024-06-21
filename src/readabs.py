"""Read time series data from the Australian Bureau of Statistics (ABS)."""

# --- imports
# system imports
from collections import namedtuple

# analytic imports
import pandas as pd

# local imports
from catalogue_map import catalogue_map
from data_capture import get_data_links


# --- constants
Metacol = namedtuple(
    "Metacol",
    [
        "did",
        "stype",
        "id",
        "start",
        "end",
        "num",
        "unit",
        "dtype",
        "freq",
        "cmonth",
        "table",
        "tdesc",
        "cat",
    ],
)
metacol = Metacol(
    did="Data Item Description",
    stype="Series Type",
    id="Series ID",
    start="Series Start",
    end="Series End",
    num="No. Obs.",
    unit="Unit",
    dtype="Data Type",
    freq="Freq.",
    cmonth="Collection Month",
    table="Table",
    tdesc="Table Description",
    cat="Catalogue number",
)


# --- functions
def print_abs_catalogue() -> None:
    """Print the ABS catalogue."""
    catalogue = catalogue_map()
    print(catalogue.loc[:, catalogue.columns != 'URL'].to_markdown())


