"""Test the read_abs_cat.py module.

Specifically test reading a single excel file and a single zip file."""

print("\n\n")
print("=" * 80)
print("Testing read_abs_cat() 3")
print("=" * 80)


import readabs as ra


# Test downloading a single table from the labour force survey
d, m = ra.read_abs_cat(cat="6202.0", single_excel_only="6202001")
print(len(d), len(m), "\n")

# Test downloading just the zip file from the lab
d, m = ra.read_abs_cat(cat="6202.0", single_zip_only="6202_all_monthly_spreadsheets")
print(len(d), len(m), "\n")
