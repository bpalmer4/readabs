"""Test the read_abs_cat.py module.

Test for every ABS catalogue number."""

import time
import sys

sys.path.append("../src")

import readabs as ra
from abs_catalogue_map import catalogue_map

WIDTH = 20  # characters
SNOOZE = 5  # seconds

cm = catalogue_map()
for row, data in cm.T.items():
    print("=" * WIDTH)
    print(row, data.iloc[:3].to_list())
    abs_dict, meta = ra.read_abs_cat(row, verbose=True, ignore_errors=True)

    print("-" * WIDTH)
    print(f"{len(abs_dict)} timeseries data tables found,")
    print(f"{len(meta)} meta data items found.")

    time.sleep(SNOOZE)  # be a little bit nice to the ABS servers

print("=" * WIDTH)
