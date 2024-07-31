"""Recalibrate a Series or DataFrame so the data is in the range -1000 to 1000."""

# --- imports
import sys
from operator import mul, truediv

from pandas import Series, DataFrame
import numpy as np

from readabs.datatype import Datatype as DataT


# --- public
def recalibrate(
    data: DataT,
    units: str,
) -> tuple[DataT, str]:
    """Recalibrate a Series or DataFrame so the data in in the range -1000 to 1000.
    Change the name of the units to reflect the recalibration.

    Note, DataT = TypeVar("DataT", Series, DataFrame). DataT is a constrained typevar.
    If you provide a Series, you will get a Series back. If you provide a DataFrame,
    you will get a DataFrame back.

    Parameters
    ----------
    data : Series or DataFrame
        The data to recalibrate.
    units : str
        The units of the data. This string should be in the form of
        "Number", "Thousands", "Millions", "Billions", etc. The units
        should be in title case.

    Returns
    -------
    Series or DataFrame
        The recalibrated data will be a Series if a Series was provided,
        or a DataFrame if a DataFrame was provided.

    Examples
    --------
    ```python
    from pandas import Series
    from readabs import recalibrate
    s = Series([1_000, 10_000, 100_000, 1_000_000])
    recalibrated, units = recalibrate(s, "$")
    print(f"{recalibrated=}, {units=}")
    ```"""

    if not isinstance(data, (Series, DataFrame)):
        raise TypeError("data must be a Series or DataFrame")
    units, restore_name = _prepare_units(units)
    flat_data = data.to_numpy().flatten()
    flat_data, units = _recalibrate(flat_data, units)

    if restore_name:
        units = f"{restore_name} {units}"
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


def recalibrate_value(value: float, units: str) -> tuple[float, str]:
    """Recalibrate a floating point value. The value will be recalibrated
    so it is in the range -1000 to 1000. The units will be changed to reflect
    the recalibration.

    Parameters
    ----------
    value : float
        The value to recalibrate.
    units : str
        The units of the value. This string should be in the form of
        "Number", "Thousands", "Millions", "Billions", etc. The units
        should be in title case.

    Returns
    -------
    tuple[float, str]
        A tuple containing the recalibrated value and the recalibrated units.

    Examples
    --------
    ```python
    from readabs import recalibrate_value
    recalibrated, units = recalibrate_value(10_000_000, "Thousand")
    print(recalibrated, units)
    ```"""

    series = Series([value])
    output, units = recalibrate(series, units)
    return output.values[0], units


# --- private
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


def _prepare_units(units: str) -> tuple[str, str]:
    """Prepare the units for recalibration."""

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

    return units, pu if found else ""


def _find_calibration(units: str) -> str | None:
    found = None
    for keyword in _keywords:
        if keyword in units or keyword.lower() in units:
            found = keyword
            break
    return found


# private
def _perfect_already(data: np.ndarray) -> bool:
    """No need to recalibrate if the data is already perfect."""
    check_max = np.nanmax(np.abs(data))
    return 1 <= check_max < 1000


def _all_zero(data: np.ndarray) -> bool:
    """Cannot recalibrate if all the data is zero."""
    if np.nanmax(np.abs(data)) == 0:
        print("recalibrate(): All zero data")
        return True
    return False


def _not_numbers(data: np.ndarray) -> bool:
    """Cannot recalibrate if the data is not numeric."""
    if (
        (not np.issubdtype(data.dtype, np.number))
        or np.isinf(data).any()
        or np.isnan(data).all()
    ):
        print("recalibrate(): Data is partly or completely non-numeric.")
        return True
    return False


def _can_recalibrate(flat_data: np.ndarray, units: str) -> bool:
    """Check if the data can be recalibrated."""

    if _find_calibration(units) is None:
        print(f"recalibrate(): Units not appropriately calibrated: {units}")
        return False

    for f in (_not_numbers, _all_zero, _perfect_already):
        if f(flat_data):
            return False

    return True


def _recalibrate(flat_data: np.ndarray, units: str) -> tuple[np.ndarray, str]:
    """Recalibrate the data.  Loop over the data until
    its maximum value is between -1000 and 1000."""

    if _can_recalibrate(flat_data, units):
        while True:
            maximum = np.nanmax(np.abs(flat_data))
            if maximum >= 1000:
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
    return flat_data, units


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


# --- test
if __name__ == "__main__":

    def test_example():
        """Test the example in the docstring."""

        s = Series([1_000, 10_000, 100_000, 1_000_000])
        recalibrated, units = recalibrate(s, "$")
        print(f"{recalibrated=}, {units=}")

        recalibrated, units = recalibrate_value(10_000_000, "Thousand")
        print(f"{recalibrated=}, {units=}")
        print("=" * 40)

    test_example()

    def test_recalibrate():
        """Test the recalibrate() function."""

        def run_test(dataset: tuple[tuple[list[str], str]]) -> None:
            for d, u in dataset:
                data = Series(d)
                recalibrated, units = recalibrate(data, u)
                print(f"{data.values}, {u} ==> {recalibrated.values}, {units}")
                print("=" * 40)

        # good examples
        good = (
            ([1, 2, 3, 4, 5], "Number"),  # no change
            ([1_000, 10_000, 100_000, 1_000_000], "$"),
            ([1_000, 10_000, 100_000, 1_000_000], "Number Spiders"),
            ([1_000, 10_000, 100_000, 1_000_000], "Thousand"),
            ([0.2, 0.3], "Thousands"),
            ([0.000_000_2, 0.000_000_3], "Trillion"),
        )
        run_test(good)

        # bad sets of data - should produce error messages and do nothing
        bad = (
            ([1, 2, 3, 4, 5], "Hundreds"),
            ([0, 0, 0], "Thousands"),
            ([np.nan, 0, 0], "Thousands"),
            ([np.inf, 1, 2], "Thousands"),
            ([0, 0, "a"], "Thousands"),
        )
        run_test(bad)

    test_recalibrate()

    def test_recalibrate_value():
        """Test the recalibrate_value() function."""

        # good example
        recalibrated, units = recalibrate_value(10_000_000, "Thousand")
        print(recalibrated, units)
        print("=" * 40)

        # bad example
        recalibrated, units = recalibrate_value(3_900, "Spiders")
        print(recalibrated, units)
        print("=" * 40)

    test_recalibrate_value()
