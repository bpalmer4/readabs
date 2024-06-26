"""Test the get_data_links() in readabs.py package.

Focus on historical data."""

print("\n\n")
print("=" * 80)
print("Testing get_data_links() 2")
print("=" * 80)

import readabs as ra

cat_map = ra.catalogue_map()
url = cat_map.loc["6202.0", "URL"]
print("ABS landing page for the labor force survey:", url)


# Get un-aged links
print("Original links:")
print(ra.get_data_links(url))

# Get aged links
print("Aged links:")
print(ra.get_data_links(url, history="dec-2023"))
