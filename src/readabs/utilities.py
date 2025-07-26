"""Utilities for working with ABS timeseries data."""

from typing import cast

from numpy import nan
from pandas import DataFrame, DatetimeIndex, PeriodIndex, Series

from readabs.datatype import Datatype as DataT

# --- constants
MONTHS_IN_YEAR = 12
QUARTERS_IN_YEAR = 4
MONTHS_IN_QUARTER = 3


# --- exceptions
class UtilitiesError(Exception):
    """Base exception for utilities module."""


class InvalidDataError(UtilitiesError):
    """Raised when input data is invalid for the operation."""


class InvalidParameterError(UtilitiesError):
    """Raised when function parameters are invalid."""


# --- functions
def percent_change(data: DataT, n_periods: int) -> DataT:
    """Calculate a percentage change in a contiguous, ordered series over n_periods.

    Args:
        data : pandas Series or DataFrame
            The data to calculate the percentage change for.
        n_periods : int
            The number of periods to calculate the percentage change over.
            Typically 4 for quarterly data, and 12 for monthly data.

    Returns:
        pandas Series or DataFrame - The percentage change in the data over n_periods.
            For DataFrame input, the percentage change is calculated for each column.

    Raises:
        InvalidParameterError - If n_periods is not a positive integer.
        InvalidDataError - If data is not a Series or DataFrame.

    """
    if not isinstance(n_periods, int) or n_periods <= 0:
        raise InvalidParameterError("n_periods must be a positive integer")

    if not isinstance(data, (Series, DataFrame)):
        raise InvalidDataError("data must be a pandas Series or DataFrame")

    try:
        return (data / data.shift(n_periods) - 1) * 100
    except Exception as e:
        raise InvalidDataError(f"Error calculating percentage change: {e}") from e


def annualise_rates(data: DataT, *, periods_per_year: float) -> DataT:
    """Annualise a growth rate for a period.

    Note: returns a percentage value (and not a rate)!

    Args:
        data : pandas Series or DataFrame - The growth rate to annualise.
            Note a growth rate of 0.05 is 5%.
        periods_per_year : int or float, default 12 - The number of periods in a year.
            For monthly data, this is 12.

    Returns:
        pandas Series or DataFrame - The annualised growth expressed as a percentage
            (not a rate). For DataFrame input, the annualised growth rate is
            calculated for each column.

    Raises:
        InvalidParameterError - If periods_per_year is not positive.
    InvalidDataError - If data is not a Series or DataFrame.

    """
    if not isinstance(data, (Series, DataFrame)):
        raise InvalidDataError("data must be a pandas Series or DataFrame")

    if not isinstance(periods_per_year, (int, float)) or periods_per_year <= 0:
        raise InvalidParameterError("periods_per_year must be a positive number")

    try:
        return (((1 + data) ** periods_per_year) - 1) * 100
    except Exception as e:
        raise InvalidDataError(f"Error annualising rates: {e}") from e


def annualise_percentages(data: DataT, *, periods_per_year: float) -> DataT:
    """Annualise a growth rate (expressed as a percentage) for a period.

    Args:
        data : pandas Series or DataFrame - The growth rate (expressed as a
            percentage) to annualise. Note a growth percentage of 5% is a growth
            rate of 0.05.
        periods_per_year : int or float, default 12 - The number of periods in a
            year. For monthly data, this is 12.

    Returns:
        pandas Series or DataFrame - The annualised growth expressed as a percentage.
            For DataFrame input, the annualised growth rate is calculated for each column.

    Raises:
        InvalidParameterError - If periods_per_year is not positive.
        InvalidDataError - If data is not a Series or DataFrame.

    """
    if not isinstance(data, (Series, DataFrame)):
        raise InvalidDataError("data must be a pandas Series or DataFrame")

    if not isinstance(periods_per_year, (int, float)) or periods_per_year <= 0:
        raise InvalidParameterError("periods_per_year must be a positive number")

    try:
        rates = data / 100.0
        return annualise_rates(rates, periods_per_year=periods_per_year)
    except Exception as e:
        raise InvalidDataError(f"Error annualising percentages: {e}") from e


def qtly_to_monthly(
    data: DataT,
    *,
    interpolate: bool = True,
    limit: int | None = 2,  # only used if interpolate is True
    dropna: bool = True,
) -> DataT:
    """Convert data from Quarterly PeriodIndex to a Monthly PeriodIndex.

    Args:
        data: Series or DataFrame with quarterly PeriodIndex. Assumes the index is unique.
            The data to convert to monthly frequency.
        interpolate: bool, default True
            Whether to interpolate the missing monthly data.
        limit: int, default 2 - The maximum number of consecutive missing months
            to interpolate.
        dropna: bool, default True - Whether to drop NA data

    Returns:
        pandas Series or DataFrame - The data with a Monthly PeriodIndex.
            If interpolate is True, the missing monthly data is interpolated.
            If dropna is True, any NA data is removed.

    Raises:
        InvalidDataError - If data index is not a quarterly PeriodIndex or has issues.
        InvalidParameterError - If limit parameter is invalid.

    """
    # Validate input data
    if not isinstance(data, (Series, DataFrame)):
        raise InvalidDataError("data must be a pandas Series or DataFrame")

    if not isinstance(data.index, PeriodIndex):
        raise InvalidDataError("data index must be a PeriodIndex")

    if not (data.index.freqstr and data.index.freqstr[0] == "Q"):
        raise InvalidDataError("data index must have quarterly frequency")

    if not data.index.is_unique:
        raise InvalidDataError("data index must be unique")

    if not data.index.is_monotonic_increasing:
        raise InvalidDataError("data index must be monotonic increasing")

    if limit is not None and (not isinstance(limit, int) or limit < 0):
        raise InvalidParameterError("limit must be a non-negative integer or None")

    # do the heavy lifting
    try:
        data = (
            data.set_axis(labels=data.index.to_timestamp(how="end"), axis="index", copy=True)
            .resample(rule="ME")  # adds in every missing month
            .first(min_count=1)  # generates nans for new months
            # assumes only one value per quarter (ie. unique index)
            .pipe(_set_axis_monthly_periods)
        )
    except Exception as e:
        raise InvalidDataError(f"Error in quarterly to monthly conversion: {e}") from e

    if interpolate:
        data = data.interpolate(limit_area="inside", limit=limit)
    if dropna:
        data = data.dropna()

    return data


def monthly_to_qtly(data: DataT, q_ending: str = "DEC", f: str = "mean") -> DataT:
    """Convert monthly data to quarterly data.

    This is done by taking the mean (or sum) of the three months in each quarter.
    Ignore quarters with less than or more than three months data. Drop NA items.
    Change f to "sum" for a quarterly sum.

    Args:
        data : pandas Series or DataFrame
            The data to convert to quarterly frequency.
        q_ending : str, default "DEC"
            The month in which the quarter ends. For example, "DEC" for December.
        f : str, default "mean"
            The function to apply to the three months in each quarter.
            Change to "sum" for a quarterly sum. The default is a
            quarterly mean.

    Returns:
        pandas Series or DataFrame
            The data with a quarterly PeriodIndex. If a quarter has less than
            three months data, the quarter is dropped. If the quarter has more
            than three months data, the quarter is dropped. Any NA data is removed.
        For DataFrame input, the function is applied to each column.

    Raises:
        InvalidDataError - If data is not a Series or DataFrame.
        InvalidParameterError - If q_ending or f parameters are invalid.

    """
    # Validate inputs
    if not isinstance(data, (Series, DataFrame)):
        raise InvalidDataError("data must be a pandas Series or DataFrame")

    valid_endings = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
    if q_ending.upper() not in valid_endings:
        raise InvalidParameterError(f"q_ending must be one of {valid_endings}")

    valid_aggregations = ["mean", "sum", "min", "max", "std", "var"]
    if f not in valid_aggregations:
        raise InvalidParameterError(f"f must be one of {valid_aggregations}")

    try:
        if isinstance(data, Series):
            return _monthly_to_qtly_series(data, q_ending, f)
        if isinstance(data, DataFrame):
            result_dict = {}
            for col in data.columns:
                result_dict[col] = _monthly_to_qtly_series(data[col], q_ending, f)
            return data.__class__(result_dict)
        # This should never be reached due to validation above
        raise InvalidDataError("Unexpected data type")  # noqa: TRY301
    except Exception as e:
        raise InvalidDataError(f"Error converting monthly to quarterly data: {e}") from e


# --- private helper functions
def _set_axis_monthly_periods(data: DataT) -> DataT:
    """Convert a DatetimeIndex to a Monthly PeriodIndex."""
    return data.set_axis(labels=cast("DatetimeIndex", data.index).to_period(freq="M"), axis="index")


def _monthly_to_qtly_series(data: Series, q_ending: str = "DEC", f: str = "mean") -> Series:
    """Convert a monthly Series to a quarterly Series.

    Args:
        data: Monthly Series to convert
        q_ending: Quarter ending month
        f: Aggregation function to apply

    Returns:
        Series: Quarterly Series with complete quarters only

    """
    try:
        return (
            data.groupby(PeriodIndex(data.index, freq=f"Q-{q_ending.upper()}"))
            .agg([f, "count"])
            .apply(lambda x: x[f] if x["count"] == MONTHS_IN_QUARTER else nan, axis=1)
            .dropna()
        )
    except Exception as e:
        raise InvalidDataError(f"Error in quarterly conversion: {e}") from e
