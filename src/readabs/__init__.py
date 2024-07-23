"""Package to download timeseries data from 
the Australian Bureau of Statistics (ABS) 
and the Reserve Bank of Australia (RBA)."""

from . import readabs
from .readabs import *

__version__ = "0.0.15a1"

__all__ = (
    # -- abs -- related
    "metacol",
    "read_abs_cat",
    "read_abs_series",
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
    "percent_change",
    "annualise_rates",
    "annualise_percentages",
    "qtly_to_monthly",
    "monthly_to_qtly",
    "recalibrate",
    "recalibrate_value",
)
