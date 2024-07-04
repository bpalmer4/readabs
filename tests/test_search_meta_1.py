"""Test the search_meta.py module.

Download the monthly labour force survey."""

print("\n\n")
print("=" * 80)
print("Testing search_meta() 1")
print("=" * 80)


import readabs as ra
from readabs import metacol

# data retrieval
print("=" * 20)
data, meta = ra.read_abs_cat(cat="6202.0", ignore_errors=True, verbose=False)
print("=" * 20)

# overview
print(f"There are {len(data)} data tables.")
print(f"The names of the data tables are: {data.keys()}.")
print("-" * 20)

search = {
    "Unemployment rate ;  Persons ;": metacol.did,
    "6202001": metacol.table,
    "Seasonally Adjusted": metacol.stype,
}
ue_meta = ra.search_meta(meta, search)
print(ue_meta.T)


