# readabs

readabs is an open-source python package to download timeseries data from
the Australian Bureau of Statistics (ABS) into a pandas DataFrame.

## Usage:

...
import readabs as ra
from readabs import metacol  # short names for meta data DataFrames
...

...
ra.print_cat_ids()
...
Print a list of available catalogue identifiers from the ABS

...
abs_dict, meta_ = ra.read_abs_cat(cat="id")
...
Get all of the data tables associated with a particular catalogue identifier.
The cat id is a string with the standard ABS identifier. For example, the 
catalog identifier for the monthly labour force survey is "".
Returns a tuple. The first element of the tuple is a dictionary of DataFrames.
The second element is a DataFrame for the meta data.

...
data, meta = ra.read_abs_series(cat="id", series="id1")
data, meta = ra.read_abs_series(cat="id", series=("id1", "id2, ...))
...
Get two DataFrames in a tuple, the first containing the data, and the
second containing the meta data for one or more ABS series identifiers.

...
data, meta = ra.read_abs_pairs(pairs={"series_id": "cat_id", })
...
Get two DataFrames in a tuple, the first containing the data, and the 
second containing the meta data, for a series of ABS series identifiers
from different ABS catalogues.


## Notes:

 * ABS data tables are downloaded and stored in a cache. By default the cache
   directory is "./.readabs" You can change the default directory name by setting
   the environemnt variable "READABS_CACHE_DIR" with the name of the preferred directory.

