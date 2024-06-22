import sys
sys.path.append('../src')

import readabs as ra

print('=' * 20)
data, meta = ra.read_abs_cat(cat="8701.0", ignore_errors=True, verbose=True)
print('=' * 20)

print(f"There are {len(data)} data tables.")
print(f"The names of the data tables are: {data.keys()}.") 
print(f"Shape of the meta data: {meta.shape}")
for name, row in zip(['First', 'Last'], [0, -1]):
    print(f"\n{name} row of meta data: {meta.iloc[row]}")



