"""utilities.py

This module provides a small numer of utilities for
working with ABS timeseries data."""

# --- imports
from typing import TypeVar, Optional, cast
from pandas import Series, DataFrame, PeriodIndex, DatetimeIndex
from numpy import nan

# - define a useful typevar for working with both Series and DataFrames
DataT = TypeVar("DataT", Series, DataFrame)


# --- functions
def percent_change(data: DataT, m_periods: int) -> DataT:
    """Calculate an percentage change in a series over n_periods."""

    return (data / data.shift(m_periods) - 1) * 100


def annualise_rates(data: DataT, periods_per_year: int | float = 12) -> DataT:
    """Annualise a growth rate for a period.
    Note: returns a percentage (and not a rate)!"""

    return (((1 + data) ** periods_per_year) - 1) * 100


def annualise_percentages(data: DataT, periods_per_year: int | float = 12) -> DataT:
    """Annualise a growth rate (expressed as a percentage) for a period."""

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

    Arguments:
    ==========
    data - either a pandas Series or DataFrame - assumes the index is unique.
    interpolate - whether to interpolate the missing monthly data.
    dropna - whether to drop NA data

    Notes:
    ======
    Necessitated by Pandas 2.2, which removed .resample()
    from pandas objects with a PeriodIndex."""

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
    """Convert monthly data to quarterly data by taking the mean of
    the three months in each quarter. Ignore quarters with less than
    three months data. Drop NA items. Change f to "sum" for a quarterly sum"""

    return (
        data.groupby(PeriodIndex(data.index, freq=f"Q-{q_ending}"))
        .agg([f, "count"])
        .apply(lambda x: x["mean"] if x["count"] == 3 else nan, axis=1)
        .dropna()
    )
