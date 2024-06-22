import time
import sys
sys.path.append('../src')

import readabs as ra
from abs_catalogue_map import catalogue_map

width = 20
cm = catalogue_map()
for row, data in cm.T.items():
    print('=' * width)
    print(row, data.iloc[:3].to_list())
    abs_dict, meta = ra.read_abs_cat(row, ignore_errors=True, verbose=True)

    print("-" * width)
    print(f"{len(abs_dict)} timeseries data tables found,")
    print(f"{len(meta)} meta data items found.")

    time.sleep(5)  # be a little bit nice to the ABS servers
print('=' * width)

