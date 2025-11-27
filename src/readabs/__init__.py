"""Package to download timeseries data from the Australian Bureau of Statistics and RBA.

This package provides functions to download and process timeseries data from
the Australian Bureau of Statistics (ABS) and the Reserve Bank of Australia (RBA).
"""

import importlib.metadata

# ABS related imports
from readabs.abs_catalogue import abs_catalogue
from readabs.abs_meta_data import metacol

# Utility imports
from readabs.datatype import Datatype
from readabs.grab_abs_url import grab_abs_url, grab_abs_zip
from readabs.print_abs_catalogue import print_abs_catalogue

# RBA related imports
from readabs.rba_catalogue import print_rba_catalogue, rba_catalogue
from readabs.rba_meta_data import rba_metacol
from readabs.read_abs_by_desc import read_abs_by_desc
from readabs.read_abs_cat import read_abs_cat
from readabs.read_abs_series import read_abs_series
from readabs.read_rba_table import read_rba_ocr, read_rba_table
from readabs.read_support import ReadArgs
from readabs.recalibrate import recalibrate, recalibrate_value
from readabs.search_abs_meta import find_abs_id, search_abs_meta
from readabs.utilities import (
    annualise_percentages,
    annualise_rates,
    monthly_to_qtly,
    percent_change,
    qtly_to_monthly,
)

# Version and author information
try:
    __version__ = importlib.metadata.version(__name__)
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.0.0"  # Fallback for development mode
__author__ = "Bryan Palmer"


# Exposed functions and classes
__all__ = (
    "Datatype",
    "ReadArgs",
    "abs_catalogue",
    "annualise_percentages",
    "annualise_rates",
    "find_abs_id",
    "grab_abs_url",
    "grab_abs_zip",
    "metacol",
    "monthly_to_qtly",
    "percent_change",
    "print_abs_catalogue",
    "print_rba_catalogue",
    "qtly_to_monthly",
    "rba_catalogue",
    "rba_metacol",
    "read_abs_by_desc",
    "read_abs_cat",
    "read_abs_series",
    "read_rba_ocr",
    "read_rba_table",
    "recalibrate",
    "recalibrate_value",
    "search_abs_meta",
)
__pdoc__ = {
    "download_cache": False,
    "get_abs_links": False,
    "read_support": False,
    "grab_abs_url": False,
}  # hide submodules from documentation
