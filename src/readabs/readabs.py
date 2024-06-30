"""Read time series data from the Australian Bureau of Statistics (ABS)."""

# --- imports
# system imports

# analytic imports

# local imports
if __package__ is None or __package__ == "":
    from search_meta import search_meta, find_id
    from abs_catalogue_map import catalogue_map
    from get_data_links import get_data_links
    from read_abs_cat import read_abs_cat
    from read_abs_series import read_abs_series
    from abs_meta_data_support import metacol
    from read_support import check_kwargs, get_args
    from utilities import (
        percent_change,
        annualise_rates,
        annualise_percentages,
        qtly_to_monthly,
        monthly_to_qtly,
        recalibrate,
        recalibrate_value,
    )
else:
    from .search_meta import search_meta, find_id
    from .abs_catalogue_map import catalogue_map
    from .get_data_links import get_data_links
    from .read_abs_cat import read_abs_cat
    from .read_abs_series import read_abs_series
    from .abs_meta_data_support import metacol
    from .read_support import check_kwargs, get_args
    from .utilities import (
        percent_change,
        annualise_rates,
        annualise_percentages,
        qtly_to_monthly,
        monthly_to_qtly,
        recalibrate,
        recalibrate_value,
    )

_ = (
    # silence linters/checkers
    get_data_links,
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
)


# --- functions
def print_abs_catalogue() -> None:
    """Print the ABS catalogue."""
    catalogue = catalogue_map()
    print(catalogue.loc[:, catalogue.columns != "URL"].to_markdown())
