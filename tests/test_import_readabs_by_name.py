"""A quick test that the import mechanism works."""

import readabs as ra

print(dir(ra))

print(f"Version: {ra.__version__}")

# extract just one series (employed total persons (thousands))
d, m = ra.read_abs_series(
    cat="6202.0", series_id="A84423043C", single_excel_only="6202001"
)
print(f"Number of observations: {d["A84423043C"].count()}")
print(f"Meta data: {m[ra.metacol.num].astype(int).iloc[0]}")
