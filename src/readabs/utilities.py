"""This module provides a small numer of utilities for
working with ABS timeseries data."""

# --- imports
from typing import Optional, cast
from numpy import nan
from pandas import Series, DataFrame, PeriodIndex, DatetimeIndex
from readabs.datatype import Datatype as DataT


# --- functions
def percent_change(data: DataT, n_periods: int) -> DataT:
    """Calculate an percentage change in a contiguous, ordered series over n_periods.

    Parameters
    ----------
    data : pandas Series or DataFrame
        The data to calculate the percentage change for.
    n_periods : int
        The number of periods to calculate the percentage change over.
        Typically 4 for quarterly data, and 12 for monthly data.

    Returns
    -------
    pandas Series or DataFrame
        The percentage change in the data over n_periods. For DataFrame input,
        the percentage change is calculated for each column.
    """

    return (data / data.shift(n_periods) - 1) * 100


def annualise_rates(data: DataT, periods_per_year: int | float = 12) -> DataT:
    """Annualise a growth rate for a period.
    Note: returns a percentage value (and not a rate)!

    Parameters
    ----------
    data : pandas Series or DataFrame
        The growth rate to annualise. Note a growth rate of 0.05 is 5%.
    periods_per_year : int or float, default 12
        The number of periods in a year. For monthly data, this is 12.

    Returns
    -------
    pandas Series or DataFrame
        The annualised growth expressed as a percentage (not a rate).
        For DataFrame input, the annualised growth rate is calculated
        for each column."""
    return (((1 + data) ** periods_per_year) - 1) * 100


def annualise_percentages(data: DataT, periods_per_year: int | float = 12) -> DataT:
    """Annualise a growth rate (expressed as a percentage) for a period.

    Parameters
    ----------
    data : pandas Series or DataFrame
        The growth rate (expresed as a percentage) to annualise. Note a
        growth percentage of 5% is a growth rate of 0.05.
    periods_per_year : int or float, default 12
        The number of periods in a year. For monthly data, this is 12.

    Returns
    -------
    pandas Series or DataFrame
        The annualised growth expressed as a percentage. For DataFrame input,
        the annualised growth rate is calculated for each column."""

    rates = data / 100.0
    return annualise_rates(rates, periods_per_year)


def qtly_to_monthly(
    data: DataT,
    interpolate: bool = True,
    limit: Optional[int] = 2,  # only used if interpolate is True
    dropna: bool = True,
) -> DataT:
    """Convert a pandas timeseries with a Quarterly PeriodIndex to an
    timeseries with a Monthly PeriodIndex.

    Parameters
    ----------
    data - either a pandas Series or DataFrame - assumes the index is unique.
        The data to convert to monthly frequency.
    interpolate: bool, default True
        Whether to interpolate the missing monthly data.
    limit: int, default 2
        The maximum number of consecutive missing months to interpolate.
    dropna: bool, default True
        Whether to drop NA data

    Returns
    -------
    pandas Series or DataFrame
        The data with a Monthly PeriodIndex. If interpolate is True, the
        missing monthly data is interpolated. If dropna is True, any NA
        data is removed."""

    # sanity checks
    assert isinstance(data.index, PeriodIndex)
    assert data.index.freqstr[0] == "Q"
    assert data.index.is_unique
    assert data.index.is_monotonic_increasing

    def set_axis_monthly_periods(x: DataT) -> DataT:
        """Convert a DatetimeIndex to a Monthly PeriodIndex."""

        return x.set_axis(
            labels=cast(DatetimeIndex, x.index).to_period(freq="M"), axis="index"
        )

    # do the heavy lifting
    data = (
        data.set_axis(
            labels=data.index.to_timestamp(how="end"), axis="index", copy=True
        )
        .resample(rule="ME")  # adds in every missing month
        .first(min_count=1)  # generates nans for new months
        # assumes only one value per quarter (ie. unique index)
        .pipe(set_axis_monthly_periods)
    )

    if interpolate:
        data = data.interpolate(limit_area="inside", limit=limit)
    if dropna:
        data = data.dropna()

    return data


def monthly_to_qtly(data: DataT, q_ending="DEC", f: str = "mean") -> DataT:
    """Convert monthly data to quarterly data by taking the mean (or sum)
    of the three months in each quarter. Ignore quarters with less than
    or more than three months data. Drop NA items. Change f to "sum"
    for a quarterly sum.

    Parameters
    ----------
    data : pandas Series or DataFrame
        The data to convert to quarterly frequency.
    q_ending : str, default DEC
        The month in which the quarter ends. For example, "DEC" for December.
    f : str, default "mean"
        The function to apply to the three months in each quarter.
        Change to "sum" for a quarterly sum. The default is a
        quarterly mean.

    Returns
    -------
    pandas Series or DataFrame
        The data with a quarterly PeriodIndex. If a quarter has less than
        three months data, the quarter is dropped. If the quarter has more
        than three months data, the quarter is dropped. Any NA data is removed.
        For DataFrame input, the function is applied to each column."""

    if isinstance(data, Series):
        return _monthly_to_qtly_series(data, q_ending, f)

    if isinstance(data, DataFrame):
        chamber = {}
        for col in data.columns:
            chamber[col] = _monthly_to_qtly_series(data[col], q_ending, f)
        return DataFrame(chamber)

    raise ValueError("data must be a pandas Series or DataFrame")


# --- private helper functions
def _monthly_to_qtly_series(data: Series, q_ending="DEC", f: str = "mean") -> Series:
    """Convert a monthly Series to a quarterly Series."""

    return (
        data.groupby(PeriodIndex(data.index, freq=f"Q-{q_ending.upper()}"))
        .agg([f, "count"])
        .apply(lambda x: x[f] if x["count"] == 3 else nan, axis=1)
        .dropna()
    )
