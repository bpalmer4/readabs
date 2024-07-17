"""This module exposes the functions necessary to read Australian data."""

# --- imports
# local imports
from .search_abs_meta import search_abs_meta, find_abs_id
from .abs_catalogue_map import abs_catalogue
from .read_abs_cat import read_abs_cat
from .read_abs_series import read_abs_series
from .grab_abs_url import grab_abs_url
from .abs_meta_data_support import metacol
from .get_rba_links import print_rba_catalogue, rba_catalogue
from .read_rba_table import read_rba_table, rba_metacol, read_rba_ocr
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
    catalogue = abs_catalogue()
    print(catalogue.loc[:, catalogue.columns != "URL"].to_markdown())


# --- syntactic sugar to silence linters
_ = (
    # silence linters/checkers
    # -- utilities --
    percent_change,
    annualise_rates,
    annualise_percentages,
    qtly_to_monthly,
    monthly_to_qtly,
    recalibrate,
    recalibrate_value,
    # -- abs -- related
    metacol,
    read_abs_cat,
    read_abs_series,
    search_abs_meta,
    find_abs_id,
    grab_abs_url,
    # -- rba -- related
    print_rba_catalogue,
    rba_catalogue,
    read_rba_table, 
    rba_metacol, 
    read_rba_ocr
)
