"""Test the read_abs_cat.py module."""

import sys
sys.path.append('../src')

import readabs as ra

# data retrieval
print('=' * 20)
data, meta = ra.read_abs_cat(cat="6202.0", ignore_errors=True, verbose=True)
print('=' * 20)

# overview
print(f"There are {len(data)} data tables.")
print(f"The names of the data tables are: {data.keys()}.") 
print('-' * 20)

# the first data table
first = data[list(data.keys())[0]]
print(f"Head of first table:\n{first.head()}")
print(f"Taik of first table:\n{first.tail()}")
print('-' * 20)

# the meta data
print(f"Shape of the meta data: {meta.shape}")
for name, row in zip(['First', 'Last'], [0, -1]):
    print(f"\n{name} row of meta data: {meta.iloc[row]}")
    print('-' * 20)
print('=' * 20)

