"""Test the read_abs_series.py module.

Specifically test reading a single excel file
both the current and previous/historical version.

Example: changes in the trend unemployment rate."""

print("\n\n")
print("=" * 80)
print("Testing read_abs_series() 2")
print("=" * 80)


from pandas import DataFrame

import readabs as ra


# latest data
d, m = ra.read_abs_series(
    cat="6202.0",
    series_id="A84423134K",  # Unemployment rate - persons - Trend
    single_excel_only="6202001",
)
current = d.index[-1].strftime("%b-%Y").lower()

# get ABS historical data pervious period
historical = (d.index[-1] - 1).strftime("%b-%Y").lower()
dh, mh = ra.read_abs_series(
    cat="6202.0",
    series_id="A84423134K",  # Unemployment rate - persons - Trend
    single_excel_only="6202001",
    history=historical,
)
print(
    DataFrame(
        {f"latest {current}": d.A84423134K, f"previous {historical}": dh.A84423134K}
    ).tail(15)
)
