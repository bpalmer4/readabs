# readabs



---


## Usage:


Standand import arrangements 
```python
import readabs as ra
from readabs import metacol  # short column names for meta data DataFrames
```


Print a list of available catalogue identifiers from the ABS
```python
ra.print_abs_catalogue()
```


Get all of the data tables associated with a particular catalogue identifier.
The catalogue identifier is a string with the standard ABS identifier. For example, 
the cataloge identifier for the monthly labour force survey is "6202.0".
Returns a tuple. The first element of the tuple is a dictionary of DataFrames.
The second element is a DataFrame for the meta data.
```python
abs_dict, meta = ra.read_abs_cat(cat="id")
```


Get two DataFrames in a tuple, the first containing the data, and the
second containing the meta data for one or more ABS series identifiers.
```python
data, meta = ra.read_abs_series(cat="id", series="id1")
data, meta = ra.read_abs_series(cat="id", series=("id1", "id2, ...))
```


Get two DataFrames in a tuple, the first containing the data, and the 
second containing the meta data, for a series of ABS series identifiers
from different ABS catalogues.
```python
data, meta = ra.read_abs_pairs(pairs={"series_id": "cat_id", })
```


---


## Notes:

 * ABS data tables are downloaded and stored in a cache. By default the cache
   directory is "./.readabs_cache/" You can change the default directory name by setting
   the environemnt variable "READABS_CACHE_DIR" with the name of the preferred directory.

