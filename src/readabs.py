"""Read time series data from the Australian Bureau of Statistics (ABS)."""

# --- imports
# system imports

# analytic imports

# local imports
from abs_catalogue_map import catalogue_map
from read_abs_cat import (
    # makes these available to the user
    get_data_links,
    read_abs_cat,
)
from abs_meta_data_support import metacol

_ = (get_data_links, read_abs_cat, metacol)  # silence linters/checkers


# --- functions
def print_abs_catalogue() -> None:
    """Print the ABS catalogue."""
    catalogue = catalogue_map()
    print(catalogue.loc[:, catalogue.columns != "URL"].to_markdown())
