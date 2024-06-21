import sys
sys.path.append('../src')

import readabs as ra

data, meta = ra.read_abs_cat(cat="5206.0", verbose=False)

print(f"There are {len(data)} data tables.")
print(f"The names of the data tables are: {data.keys()}.") 
print(f"Shape of the meta data: {meta.shape}")
