"""Test the monthly-frequency guard on utilities.monthly_to_qtly().

Non-monthly data used to be silently converted to an empty (or near-empty)
result. It now raises InvalidDataError, unless the data has a monthly PeriodIndex.

The rejection tests match the guard's own message, not just the exception type:
monthly_to_qtly() wraps any conversion failure in InvalidDataError, so some bad
inputs raised InvalidDataError even before the guard existed.

These tests are hermetic: no network access is made.
"""

from collections.abc import Callable

from pandas import DataFrame, Series, date_range, period_range

from readabs.utilities import InvalidDataError, monthly_to_qtly

# --- constants
GUARD_MESSAGE = "data must have a monthly PeriodIndex"
MONTHLY = Series(
    [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0],  # Q3 has only July - so it is dropped
    index=period_range("2024-01", periods=7, freq="M"),
)


# --- helpers
def _guard_message(func: Callable[[], object]) -> str:
    """Return the InvalidDataError message raised by func, or '' if none is raised."""
    try:
        func()
    except InvalidDataError as e:
        return str(e)
    return ""


def _assert_rejected(data: Series, freq: str) -> None:
    """Assert that the guard (not a later failure) rejects data, naming its frequency."""
    message = _guard_message(lambda: monthly_to_qtly(data))
    assert GUARD_MESSAGE in message, message
    assert freq in message, message


# --- tests: non-monthly data is rejected by the guard
def test_quarterly_rejected() -> None:
    """Quarterly data - previously an empty result - is rejected."""
    _assert_rejected(Series([1.0, 2.0], index=period_range("2024Q1", periods=2, freq="Q")), "'Q-DEC'")


def test_daily_rejected() -> None:
    """Daily data - previously a near-empty result - is rejected."""
    _assert_rejected(Series([1.0, 2.0], index=period_range("2024-01-01", periods=2, freq="D")), "'D'")


def test_monthly_datetime_index_rejected() -> None:
    """A monthly DatetimeIndex - previously accepted - is rejected."""
    _assert_rejected(Series([1.0, 2.0], index=date_range("2024-01-31", periods=2, freq="ME")), "DatetimeIndex")


def test_range_index_rejected() -> None:
    """A plain integer index is rejected by the guard."""
    _assert_rejected(Series([1.0, 2.0]), "RangeIndex")


# --- tests: monthly data passes the guard, and converts as before
def test_monthly_series_accepted() -> None:
    """A monthly Series converts to complete quarters only."""
    result = monthly_to_qtly(MONTHLY)
    assert result.tolist() == [2.0, 5.0]
    assert [str(p) for p in result.index] == ["2024Q1", "2024Q2"]


def test_monthly_dataframe_accepted() -> None:
    """A monthly DataFrame converts column by column, and stays a DataFrame."""
    result = monthly_to_qtly(DataFrame({"a": MONTHLY, "b": MONTHLY * 10}), f="sum")
    assert isinstance(result, DataFrame)
    assert result.to_dict("list") == {"a": [6.0, 15.0], "b": [60.0, 150.0]}


if __name__ == "__main__":
    test_quarterly_rejected()
    test_daily_rejected()
    test_monthly_datetime_index_rejected()
    test_range_index_rejected()
    test_monthly_series_accepted()
    test_monthly_dataframe_accepted()
    print("All monthly_to_qtly guard tests passed.")
