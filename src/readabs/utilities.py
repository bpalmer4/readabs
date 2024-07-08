"""utilities.py

This module provides a small numer of utilities for
working with ABS timeseries data."""

# --- imports
import sys
from operator import mul, truediv
from typing import TypeVar, Optional, cast
import numpy as np
from numpy import nan
from pandas import Series, DataFrame, PeriodIndex, DatetimeIndex

# - define a useful typevar for working with both Series and DataFrames
DataT = TypeVar("DataT", Series, DataFrame)


# --- functions
def percent_change(data: DataT, n_periods: int) -> DataT:
    """Calculate an percentage change in a series over n_periods."""

    return (data / data.shift(n_periods) - 1) * 100


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
        .apply(lambda x: x[f] if x["count"] == 3 else nan, axis=1)
        .dropna()
    )


# --- recalibration
# private
_MIN_RECALIBRATE = "number"  # all lower case
_MAX_RECALIBRATE = "decillion"  # all lower case
_keywords = {
    _MIN_RECALIBRATE.title(): 0,
    "Thousand": 3,
    "Million": 6,
    "Billion": 9,
    "Trillion": 12,
    "Quadrillion": 15,
    "Quintillion": 18,
    "Sextillion": 21,
    "Septillion": 24,
    "Octillion": 27,
    "Nonillion": 30,
    _MAX_RECALIBRATE.title(): 33,
}
_r_keywords = {v: k for k, v in _keywords.items()}


# private
def _find_calibration(units: str) -> str | None:
    found = None
    for keyword in _keywords:
        if keyword in units or keyword.lower() in units:
            found = keyword
            break
    return found


# private
def _can_recalibrate(flat_data: np.ndarray, units: str, verbose: bool = False) -> bool:
    if not np.issubdtype(flat_data.dtype, np.number):
        print("recalibrate(): Non numeric input data")
        return False
    if np.isnan(flat_data).all():
        print("recalibrate(): All NaN data.")
        return False
    if (np.isinf(flat_data)).any():
        print("recalibrate(): Includes non-finite data.")
        return False
    if _find_calibration(units) is None:
        if verbose:
            print("recalibrate(): Units not appropriately " f"calibrated: {units}")
        return False
    if np.nanmax(np.abs(flat_data)) == 0:
        print("recalibrate(): All zero data")
        return False
    if flat_data.max() <= 1000 and flat_data.max() >= 1:
        if verbose:
            print("recalibrate(): No adjustments needed")
        return False
    return True


def _do_recal(flat_data, units, step, operator):
    calibration = _find_calibration(units)
    factor = _keywords[calibration]
    if factor + step not in _r_keywords:
        print(f"Unexpected factor: {factor + step}")
        sys.exit(-1)
    replacement = _r_keywords[factor + step]
    units = units.replace(calibration, replacement)
    units = units.replace(calibration.lower(), replacement)
    flat_data = operator(flat_data, 1000)
    return flat_data, units


def recalibrate(
    data: DataT,
    units: str,
    verbose: bool = False,
) -> tuple[DataT, str]:
    """Recalibrate a Series/DataFrame so the data in in the range -1000 to 1000."""

    # prepare the units for recalibration
    substitutions = [
    	("000 Hours", "Thousand Hours"),
    	("$'000,000", "$ Million"),
    	("$'000", " $ Thousand"),
    	("'000,000", "Millions"),
    	("'000", "Thousands"),
    	("000,000", "Millions"),
    	("000", "Thousands"),
    ]
    units = units.strip()
    for pattern, replacement in substitutions:
    	units = units.replace(pattern, replacement)

    # do the recalibration
    flat_data = data.to_numpy().flatten()

    # manage the names for some gnarly units
    possible_units = ("$", "Tonnes")  # there may be more possible units
    found = False
    for pu in possible_units:
        if pu.lower() in units.lower():
            units = units.lower().replace(pu.lower(), "").strip()
            if units == "":
                units = "number"
            found = True
            break

    if _can_recalibrate(flat_data, units, verbose):
        while True:
            maximum = np.nanmax(np.abs(flat_data))
            if maximum > 1000:
                if _MAX_RECALIBRATE in units.lower():
                    print("recalibrate() is not designed for very big units")
                    break
                flat_data, units = _do_recal(flat_data, units, 3, truediv)
                continue
            if maximum < 1:
                if _MIN_RECALIBRATE in units.lower():
                    print("recalibrate() is not designed for very small units")
                    break
                flat_data, units = _do_recal(flat_data, units, -3, mul)
                continue
            break

    if found:
        units = f"{pu} {units}"
        for n in "numbers", "number":
            if n in units:
                units = units.replace(n, "").strip()
                break
    units = units.title()

    restore_pandas = DataFrame if len(data.shape) == 2 else Series
    result = restore_pandas(flat_data.reshape(data.shape))
    result.index = data.index
    if len(data.shape) == 2:
        result.columns = data.columns
    if len(data.shape) == 1:
        result.name = data.name
    return result, units


# public
def recalibrate_value(value: float, units: str) -> tuple[float, str]:
    """Recalibrate a floating point value."""

    series = Series([value])
    output, units = recalibrate(series, units)
    return output.values[0], units
