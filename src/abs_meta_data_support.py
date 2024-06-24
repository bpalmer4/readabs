"""abs_meta_data_sypport.py

Support for working with ABS meta data."""

from collections import namedtuple

Metacol = namedtuple(
    "Metacol",
    [
        "did",
        "stype",
        "id",
        "start",
        "end",
        "num",
        "unit",
        "dtype",
        "freq",
        "cmonth",
        "table",
        "tdesc",
        "cat",
    ],
)

metacol = Metacol(
    did="Data Item Description",
    stype="Series Type",
    id="Series ID",
    start="Series Start",
    end="Series End",
    num="No. Obs.",
    unit="Unit",
    dtype="Data Type",
    freq="Freq.",
    cmonth="Collection Month",
    table="Table",
    tdesc="Table Description",
    cat="Catalogue number",
)
