"""Read a table from the RBA website and store it in a pandas DataFrame."""

from typing import Any, cast
from io import BytesIO
import re
from pandas import (
    DataFrame,
    DatetimeIndex,
    PeriodIndex,
    Period,
    Index,
    read_excel,
    Series,
    Timestamp,
    period_range,
)

# local imports
from readabs.rba_catalogue import rba_catalogue
from readabs.download_cache import get_file, HttpError, CacheError
from readabs.rba_meta_data import rba_metacol as rm


# --- PRIVATE ---
def _get_excel_file(
    table: str,
    ignore_errors: bool,
    **kwargs: Any,
) -> bytes | None:
    """Get the Excel file from the RBA website for the given table.
    Return bytes if successful, otherwise return None.
    Raises an exception if ignore_errors is False."""

    # get the relevant URL for a table moniker
    cat_map = rba_catalogue()
    if table not in cat_map.index:
        message = f"Table '{table}' not found in RBA catalogue."
        if ignore_errors:
            print(f"Ignoring error: {message}")
            return None
        raise ValueError(message)
    url = str(cat_map.loc[table, "URL"])

    # get Excel file - try different file name extensions
    # becasue the RBA website sometimes changes the file
    # extension in error
    urls = [
        url,
    ]
    rex = re.compile(r"\.[^/]*$")
    match = rex.search(url)
    if match is not None:
        tail = match.group()
        replace_with = {".xls": ".xlsx", ".xlsx": ".xls"}
        new_url = re.sub(rex, replace_with.get(tail, tail), url)
        if new_url != url:
            urls += [new_url]

    # try to get the Excel file - including with different exensions
    for this_url in urls:
        try:
            excel = get_file(this_url, **kwargs)
        except (HttpError, CacheError) as e:
            if this_url == urls[-1]:
                if ignore_errors:
                    print(f"Ignoring error: {e}")
                    return None
                raise
        else:
            break

    return excel


# --- PUBLIC ---
def read_rba_table(table: str, **kwargs: Any) -> tuple[DataFrame, DataFrame]:
    """Read a table from the RBA website and return the actual data
    and the meta data in a tuple of two DataFrames.

    Parameters
    ----------
    table : str
        The table to read from the RBA website.
    **kwargs : Any
        Additional keyword arguments.
        The only keyword argument that is used is ignore_errors.
    ignore_errors : bool = False
        If True, then any major errors encountered will be printed and the function
        will return empty DataFrames. If False, then any major errors encountered
        will raise an exception.

    Returns
    -------
    tuple[DataFrame, DataFrame]
        The primary data and the meta data in a tuple of two DataFrames.

    Examples
    --------
    ```python
    data, meta = read_rba_table("C1")
    ```"""

    # set-up
    ignore_errors = kwargs.get("ignore_errors", False)
    data, meta = DataFrame(), DataFrame()

    # get the Excel file
    excel = _get_excel_file(table, ignore_errors, **kwargs)
    if excel is None:
        return data, meta

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
    meta.columns = Index(meta.iloc[0])
    renamer = {
        "Mnemonic": rm.id,
    }  # historical data is inconsistent
    meta = meta.rename(columns=renamer)
    meta = meta.iloc[1:, :]
    meta.index = Index(meta[rm.id])
    meta[rm.table] = table
    meta[rm.tdesc] = raw.iloc[0, 0]
    meta = meta.dropna(how="all", axis=1)  # drop columns with all NaNs

    # extract the data
    data = raw.iloc[10:, :].copy()
    data.columns = Index(data.iloc[0])
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
    depending on the value of the monthly parameter. The default is monthly.

    Parameters
    ----------
    monthly : bool = True
        If True, then the data will be returned with a monthly PeriodIndex.
        If False, then the data will be returned with a daily PeriodIndex.
    **kwargs : Any
        Additional keyword arguments. The only keyword argument that is used is ignore_errors.
    ignore_errors : bool = False
        If True, then any major errors encountered will be printed and the function
        will return an empty Series. If False, then any major errors encountered
        will raise an exception.

    Returns
    -------
    Series
        The OCR data in a pandas Series, with an index of either daily or monthly Periods.

    Examples
    --------
    ```python
    ocr = read_rba_ocr(monthly=True)
    ```"""

    # read the OCR table from the RBA website, make float and sort, name the series
    rba, _rba_meta = read_rba_table("A2", **kwargs)  # should have a daily PeriodIndex
    ocr = (
        rba.loc[lambda x: x.index >= "1990-08-02", "ARBAMPCNCRT"]
        .astype(float)
        .sort_index()
    )
    ocr.name = "RBA Official Cash Rate"

    # bring up to date
    today = Period(Timestamp.today(), freq=cast(PeriodIndex, ocr.index).freqstr)
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

    def test_read_rba_table():
        """Test the read_rba_table function."""

        # test with a known table
        d, m = read_rba_table("C1")
        print(m)
        print(d.head())
        print(d.tail())
        print("=" * 20)

        # test with an unknown table
        try:
            d, m = read_rba_table("XYZ")
        except ValueError as e:
            print(e)
        print("=" * 20)

    test_read_rba_table()

    def test_read_rba_ocr():
        """Test the read_rba_ocr function."""

        # test with monthly data
        ocr = read_rba_ocr(monthly=True)
        print(ocr.head())
        print("...")
        print(ocr.tail())
        print("=" * 20)

        # test with daily data
        ocr = read_rba_ocr(monthly=False)
        print(ocr.head())
        print("...")
        print(ocr.tail())
        print("=" * 20)

    test_read_rba_ocr()
