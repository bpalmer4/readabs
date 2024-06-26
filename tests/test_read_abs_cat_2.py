"""Test the read_abs_cat.py module.

Test for every ABS catalogue number."""

print("\n\n")
print("=" * 80)
print("Testing read_abs_cat() 2")
print("=" * 80)


import time
import readabs as ra


WIDTH = 20  # characters
SNOOZE = 5  # seconds

cm = ra.catalogue_map()
for row, data in cm.T.items():
    print("=" * WIDTH)
    print(row, data.iloc[:3].to_list())
    abs_dict, meta = ra.read_abs_cat(row, verbose=True, ignore_errors=True)

    print("-" * WIDTH)
    print(f"{len(abs_dict)} timeseries data tables found,")
    print(f"{len(meta)} meta data items found.")

    time.sleep(SNOOZE)  # be a little bit nice to the ABS servers

print("=" * WIDTH)
