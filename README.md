# readabs

readabs is an open-source python package to download timeseries data from
the Australian Bureau of Statistics (ABS) into a pandas DataFrame.


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

 * This package largely does not manipulate the ABS data. If the same data_column name is 
   duplicated, then the duplicates are removed. But otherwise the data is returned as it
   was downloaded. This includes any NA-only (ie. empty) columns where they occur.
 * This package only downloads timeseries data tables. Other data tables (for example,
   pivot tables) are ignored.
 * The index for all of the downloaded tables should be a pandas PeriodIndex, with an
   appropriately set frequency. 
 * In the process of data retrieval, the ABS data tables are downloaded and stored in a 
   local cache. By default the cache directory is "./.readabs_cache/". 
   You can change the default directory name by setting the environemnt variable 
   "READABS_CACHE_DIR" with the name of the preferred directory.
 * the read functions have a number of standard keyword arguments (with default settings 
   as follows):
   - `verbose=False` - Do not print detailed information on the data retrieval process.
     Setting this to true may help diagnose why something might be going wrong with the
     data retrieval process. 
   - `get_zip=True` - Download .zip files. 
   - `get_excel_if_no_zip=True` Only try to download .xlsx files if there are no
     zip files available to be downloaded.
   - `get_excel=False` - Do not automatically download .xlsx files. 
     Note at least one of get_zip, get_excel_if_no_zip, or get_excel must be true. 
     For most ABS catalogue items, it is sufficient to just download the zip file. 
     But note, some catalogue items do not have a zip file.
   - `ignore_errors=False` - Cease downloading when a HTTP error in encounted. However,
      sometimes the ABS website has malformed links, and this setting is necessitated.
      
