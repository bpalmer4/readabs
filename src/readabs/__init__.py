"""Package to download timeseries data from 
the Australian Bureau of Statistics (ABS) 
and the Reserve Bank of Australia (RBA)."""

__version__ = "0.0.29"
__author__ = "Bryan Palmer"
__all__ = (
    # -- abs -- related
    "metacol",
    "read_abs_cat",
    "read_abs_series",
    "read_abs_by_desc",
    "search_abs_meta",
    "find_abs_id",
    "grab_abs_url",
    "print_abs_catalogue",
    "abs_catalogue",
    # -- rba -- related
    "print_rba_catalogue",
    "rba_catalogue",
    "read_rba_table",
    "rba_metacol",
    "read_rba_ocr",
    # -- utilities --
    "Datatype",
    "percent_change",
    "annualise_rates",
    "annualise_percentages",
    "qtly_to_monthly",
    "monthly_to_qtly",
    "recalibrate",
    "recalibrate_value",
)
__pdoc__ = {
    "download_cache": False,
    "get_abs_links": False,
    "read_support": False,
    "grab_abs_url": False,
}  # hide submodules from documentation


# --- local imports
# - ABS related -
from readabs.abs_catalogue import abs_catalogue
from readabs.print_abs_catalogue import print_abs_catalogue
from readabs.search_abs_meta import search_abs_meta, find_abs_id
from readabs.read_abs_cat import read_abs_cat
from readabs.read_abs_series import read_abs_series
from readabs.read_abs_by_desc import read_abs_by_desc
from readabs.grab_abs_url import grab_abs_url
from readabs.abs_meta_data import metacol

# - RBA related -
from readabs.rba_catalogue import print_rba_catalogue, rba_catalogue
from readabs.read_rba_table import read_rba_table, read_rba_ocr
from readabs.rba_meta_data import rba_metacol

# - Utilities -
from readabs.datatype import Datatype
from readabs.recalibrate import recalibrate, recalibrate_value
from readabs.utilities import (
    percent_change,
    annualise_rates,
    annualise_percentages,
    qtly_to_monthly,
    monthly_to_qtly,
)
