"""Test the keyword-argument guard on find_abs_id() and search_abs_meta().

A mistyped keyword (e.g. exact=True for exact_match=True) used to be silently
swallowed by **kwargs. It is now reported, once, and otherwise ignored.

These tests are hermetic: they search a small hand-built meta data table, so
no network access is made.

Each valid keyword is checked against a control call without it, where the
result differs - so a test only passes if the keyword actually reached
search_abs_meta(), rather than being dropped along with the bad ones.
"""

from collections.abc import Callable
from contextlib import redirect_stdout
from io import StringIO
from typing import Any, TypeVar

from pandas import DataFrame

from readabs.abs_meta_data import metacol as mc
from readabs.search_abs_meta import find_abs_id, search_abs_meta

# --- constants
TABLE = "62020001"
META = DataFrame(
    {
        mc.did: ["Unemployment rate ;  Persons ;", "Employed total ;  Persons ;", "Employed"],
        mc.id: ["A1", "B1", "C1"],
        mc.unit: ["Percent", "000", "000"],
        mc.table: [TABLE, TABLE, TABLE],
    }
)
UNEXPECTED = "Unexpected keyword argument"
BAD_KWARGS: dict[str, Any] = {"exact": True}  # typo for exact_match; a dict gets it past the type checker


T = TypeVar("T")


# --- helpers
def _capture(func: Callable[[], T]) -> tuple[T, str]:
    """Call func, returning its result and everything it printed."""
    buffer = StringIO()
    with redirect_stdout(buffer):
        result = func()
    return result, buffer.getvalue()


def _raises_value_error(func: Callable[[], object]) -> bool:
    """Return True if func raises a ValueError (its printed output is discarded)."""
    try:
        _capture(func)
    except ValueError:
        return True
    return False


# --- tests: an unknown keyword is reported
def test_find_abs_id_reports_exact() -> None:
    """exact=True is reported once, naming 'exact', and the result is as before.

    "Unemployment rate" is only a substring of the description, so an exact match
    would find nothing and raise: returning A1 shows 'exact' was ignored (as
    before), not quietly treated as exact_match.
    """
    terms = {"Unemployment rate": mc.did}
    before, _ = _capture(lambda: find_abs_id(META, terms))
    after, output = _capture(lambda: find_abs_id(META, terms, **BAD_KWARGS))
    assert after == before == (TABLE, "A1", "Percent")
    assert output.count(UNEXPECTED) == 1, output
    assert "'exact'" in output


def test_search_abs_meta_reports_exact() -> None:
    """Called directly, search_abs_meta() also reports exact=True, once."""
    rows, output = _capture(lambda: search_abs_meta(META, {"Unemployment rate": mc.did}, **BAD_KWARGS))
    assert list(rows.index) == ["A1"]
    assert output.count(UNEXPECTED) == 1, output
    assert "'exact'" in output


# --- tests: the valid keywords are silent, and take effect
def test_exact_match_is_valid() -> None:
    """exact_match=True: 'Employed' picks C1 only; without it, B1 and C1 match."""
    terms = {"Employed": mc.did}
    assert _raises_value_error(lambda: find_abs_id(META, terms))
    result, output = _capture(lambda: find_abs_id(META, terms, exact_match=True))
    assert result == (TABLE, "C1", "000")
    assert UNEXPECTED not in output


def test_regex_is_valid() -> None:
    """regex=True: the pattern matches A1; as a literal string it matches nothing."""
    terms = {"^Unemp.*rate": mc.did}
    assert _raises_value_error(lambda: find_abs_id(META, terms))
    result, output = _capture(lambda: find_abs_id(META, terms, regex=True))
    assert result == (TABLE, "A1", "Percent")
    assert UNEXPECTED not in output


def test_validate_unique_is_valid() -> None:
    """validate_unique=False: two matches return the first; the default (True) raises."""
    terms = {"Employed": mc.did}
    assert _raises_value_error(lambda: find_abs_id(META, terms))
    result, output = _capture(lambda: find_abs_id(META, terms, validate_unique=False))
    assert result == (TABLE, "B1", "000")
    assert UNEXPECTED not in output


def test_verbose_is_valid() -> None:
    """verbose=True: search_abs_meta() prints its trace; without it, nothing is printed."""
    terms = {"Unemployment rate": mc.did}
    _, quiet = _capture(lambda: find_abs_id(META, terms))
    assert not quiet
    result, output = _capture(lambda: find_abs_id(META, terms, verbose=True))
    assert result == (TABLE, "A1", "Percent")
    assert "Final selection is 1 rows." in output
    assert UNEXPECTED not in output


if __name__ == "__main__":
    test_find_abs_id_reports_exact()
    test_search_abs_meta_reports_exact()
    test_exact_match_is_valid()
    test_regex_is_valid()
    test_validate_unique_is_valid()
    test_verbose_is_valid()
    print("All search-kwargs tests passed.")
