"""Test the get_data_links() in readabs.py package.

Test over all ABS landing pages for each catalogue identifier."""

print("\n\n")
print("=" * 80)
print("Testing get_data_links() 1")
print("=" * 80)

import readabs as ra

cm = ra.catalogue_map()
print("-------------")
for row, series in cm.T.items():
    print(row, series, "\n")
    links = ra.get_data_links(series["URL"])
    print(links)
    print("-------------")
