import readabs as ra

print(dir(ra))

ra.print_abs_catalogue()

# extract just one series (employed total persons (thousands))
d, m = ra.read_abs_series(
    cat="6202.0", series_id="A84423043C", ignore_errors=True, verbose=True
)
print(d, "\n", m)

