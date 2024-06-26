"""Test the read_abs_series.py module."""

print("\n\n")
print("=" * 80)
print("Testing read_abs_series() 1")
print("=" * 80)


import readabs as ra


# extract two series (%Q/Q growth for GDP and GDP/Capita - SA, CVM $m)
d, m = ra.read_abs_series(
    cat="5206.0",
    series_id=["A2304370T", "A2304372W"],
    ignore_errors=False,
    verbose=True,
)
print(d, "\n", m)

# extract just one series (employed total persons (thousands))
d, m = ra.read_abs_series(
    cat="6202.0", series_id="A84423043C", ignore_errors=True, verbose=True
)
print(d, "\n", m)
