"""This module exposes the functions necessary to read ABS data."""

# --- imports
# local imports
from .search_meta import search_meta, find_id
from .abs_catalogue_map import catalogue_map
from .read_abs_cat import read_abs_cat
from .read_abs_series import read_abs_series
from .grab_abs_url import grab_abs_url
from .abs_meta_data_support import metacol
from .utilities import (
    percent_change,
    annualise_rates,
    annualise_percentages,
    qtly_to_monthly,
    monthly_to_qtly,
    recalibrate,
    recalibrate_value,
)


# --- functions
def print_abs_catalogue() -> None:
    """Print the ABS catalogue."""
    catalogue = catalogue_map()
    print(catalogue.loc[:, catalogue.columns != "URL"].to_markdown())


# --- syntactic sugar to silence linters
_ = (
    # silence linters/checkers
    metacol,
    read_abs_cat,
    read_abs_series,
    percent_change,
    annualise_rates,
    annualise_percentages,
    qtly_to_monthly,
    monthly_to_qtly,
    recalibrate,
    recalibrate_value,
    search_meta,
    find_id,
    grab_abs_url,
)
