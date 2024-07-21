"""read_rba_table.py

Read a table from the RBA website and store it in a pandas DataFrame."""

from collections import namedtuple
from typing import Any
from io import BytesIO
from pandas import (
    DataFrame,
    DatetimeIndex,
    PeriodIndex,
    Period,
    read_excel,
    Series,
    Timestamp,
    period_range,
)

# local imports
# multiple imports to allow for direct testing before packaging
try:
    from .get_rba_links import rba_catalogue
    from .download_cache import get_file, HttpError, CacheError
except ImportError:
    from get_rba_links import rba_catalogue
    from download_cache import get_file, HttpError, CacheError

# --- PUBLIC ---
RbaMetacol = namedtuple(
    "RbaMetacol",
    [
        "title",
        "desc",
        "freq",
        "type",
        "unit",
        "src",
        "pub",
        "id",
        "table",
        "tdesc",
    ],
)

rba_metacol = RbaMetacol(
    title="Title",
    desc="Description",
    freq="Frequency",
    type="Type",
    unit="Units",
    src="Source",
    pub="Publication date",
    id="Series ID",
    table="Table",
    tdesc="Table Description",
)


def read_rba_table(table: str, **kwargs: Any) -> tuple[DataFrame, DataFrame]:
    """Read a table from the RBA website and return the actual data
    and the meta data in a tuple of two DataFrames.

    Parameters
    ----------
    table : str
        The table to read from the RBA website.
    **kwargs : Any
        Additional keyword arguments.

    Returns
    -------
    tuple[DataFrame, DataFrame]
        The actual data and the meta data in a tuple of two DataFrames."""

    # set-up
    ignore_errors = kwargs.get("ignore_errors", False)
    data, meta = DataFrame(), DataFrame()

    # get URL
    cat_map = rba_catalogue()
    if table not in cat_map.index:
        message = f"Table '{table}' not found in RBA catalogue."
        if ignore_errors:
            print(f"Ignoring error: {message}")
            return data, meta
        raise ValueError(f"Table '{table}' not found in RBA catalogue.")
    url = cat_map.loc[table, "URL"]

    # get Excel file
    try:
        excel = get_file(url, **kwargs)
    except HttpError as e:
        if ignore_errors:
            print(f"Ignoring error: {e}")
            return data, meta
        raise
    except CacheError as e:
        if ignore_errors:
            print(f"Ignoring error: {e}")
            return data, meta
        raise

    # read Excel file into DataFrame
    try:
        raw = read_excel(BytesIO(excel), header=None, index_col=None)
    except Exception as e:
        if ignore_errors:
            print(f"Ignoring error: {e}")
            return data, meta
        raise

    # extract the meta data
    meta = raw.iloc[1:11, :].T.copy()
    meta.columns = meta.iloc[0]
    meta = meta.iloc[1:, :]
    meta.index = meta[rba_metacol.id]
    meta[rba_metacol.table] = table
    meta[rba_metacol.tdesc] = raw.iloc[0, 0]
    meta = meta.dropna(how="all", axis=1)  # drop columns with all NaNs

    # extract the data
    data = raw.iloc[10:, :].copy()
    data.columns = data.iloc[0]
    data = data.iloc[1:, :]
    data.index = DatetimeIndex(data.iloc[:, 0])
    data = data.iloc[:, 1:]
    data = data.dropna(how="all", axis=1)  # drop columns with all NaNs

    # can we make the index into a PeriodIndex?
    days = data.index.to_series().diff(1).dropna().dt.days
    if days.min() >= 28 and days.max() <= 31:
        data.index = PeriodIndex(data.index, freq="M")
    elif days.min() >= 90 and days.max() <= 92:
        data.index = PeriodIndex(data.index, freq="Q")
    elif days.min() >= 365 and days.max() <= 366:
        data.index = PeriodIndex(data.index, freq="Y")
    else:
        data.index = PeriodIndex(data.index, freq="D")

    return data, meta


def read_rba_ocr(monthly: bool = True, **kwargs: Any) -> Series:
    """Read the Official Cash Rate (OCR) from the RBA website and return it
    in a pandas Series, with either a daily or monthly PeriodIndex,
    depending on the value of the monthly parameter. The default is monthly."""

    # read the OCR table from the RBA website, make float and sort, name the series
    rba, _rba_meta = read_rba_table("A2", **kwargs)  # should have a daily PeriodIndex
    ocr = rba["ARBAMPCNCRT"]["1990-08-02":].astype(float).sort_index()
    ocr.name = "RBA Official Cash Rate"

    # bring up to date
    today = Period(Timestamp.today(), freq=ocr.index.freqstr)
    if ocr.index[-1] < today:
        ocr[today] = ocr.iloc[-1]

    if not monthly:
        # fill in missing days and return daily data
        daily_index = period_range(start=ocr.index.min(), end=ocr.index.max(), freq="D")
        ocr = ocr.reindex(daily_index).ffill()
        return ocr

    # convert to monthly data, keeping last value if duplicates in month
    # fill in missing months
    ocr.index = PeriodIndex(ocr.index, freq="M")
    ocr = ocr[~ocr.index.duplicated(keep="last")]
    monthly_index = period_range(start=ocr.index.min(), end=ocr.index.max(), freq="M")
    ocr = ocr.reindex(monthly_index, method="ffill")
    return ocr


# --- TESTING ---
if __name__ == "__main__":
    d, m = read_rba_table("C1")
    print(m)
    print(d.head())
    print(d.tail())
    print("=" * 20)

    ocr_ = read_rba_ocr()
    print(ocr_.head())
    print(ocr_.tail())
    ocr_ = read_rba_ocr(monthly=False)
    print(ocr_.head())
    print(ocr_.tail())
