"""A quick test that the import mechanism works."""

from readabs import *

# extract just one series (employed total persons (thousands))
d, m = read_abs_series(
    cat="6202.0", series_id="A84423043C", single_excel_only="6202001"
)
print(f"Number of observations: {d["A84423043C"].count()}")
print(f"Meta data: {m[metacol.num].astype(int).iloc[0]}")
