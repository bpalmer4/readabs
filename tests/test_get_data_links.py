"""Test the get_data_links() in readabs.py package."""

import sys
sys.path.append('../src')

import readabs as ra

cm = ra.catalogue_map()
print('-------------')
for row, series in cm.T.items():
    print(row, series, '\n')
    links = ra.get_data_links(series["URL"])
    print(links)
    print('-------------')

