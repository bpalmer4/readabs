# readabs

readabs is an open-source python package to download and work with 
imeseries data from the Australian Bureau of Statistics (ABS),
using pandas DataFrames.


---


## Usage:


Standand import arrangements 
```python
import readabs as ra
from readabs import metacol  # short column names for meta data DataFrames
```


Print a list of available catalogue identifiers from the ABS. You may need
this to get the catalogue identifier/number for the data you want to download.
```python
ra.print_abs_catalogue()
```


Get the ABS catalogue map as a pandas DataFrame.
```python
cat_map = ra.catalogue_map()
```


Get all of the data tables associated with a particular catalogue identifier.
The catalogue identifier is a string with the standard ABS identifier. For example, 
the cataloge identifier for the monthly labour force survey is "6202.0".
Returns a tuple. The first element of the tuple is a dictionary of DataFrames.
The dictionary is indexed by table names (which can be found in the meta data).
The second element is a DataFrame for the meta data. Note: with some ABS
catalogues, a specific series may be repeated in more than one table.
```python
abs_dict, meta = ra.read_abs_cat(cat="id")
```


Get two DataFrames in a tuple, the first containing the actual data, and the
second containing the meta data for one or more specified ABS series identifiers.
```python
data, meta = ra.read_abs_series(cat="id", series="id1")
data, meta = ra.read_abs_series(cat="id", series=("id1", "id2, ...))
```

### Additional utility functions
While not necessary for working with ABS data, the package includes some useful
functions for manipulating ABS data:

Calculate percentage change over n_periods.
```python
change_data = percentage_change(data, n_periods)
```

Annualise monthly or quarterly percentage rates.
```python
annualised = annualise_percentages(data, periods_per_year)
```

Convert a pandas timeseries with a Quarterly PeriodIndex to an
timeseries with a Monthly PeriodIndex.
```python
monthly_data = qtly_to_monthly(
    quarterly_data, 
    interpolate, # default is True
    limit,  # default is 2, only used if interpolate is True
    dropna,  # default is True,
)
```

Convert monthly data to quarterly data by taking the mean or sum of
the three months in each quarter. Ignore quarters with less than
three months data. Drop NA items. 
```python
quarterly_data = monthly_to_qtly(
    data,
    q_ending,  # default is "DEC"
    f, the func
    tion to apply ("sum" or "mean"), the default is "mean"
)
```

---

## Notes:

 * This package largely does not manipulate the ABS data. The data is returned as it
   was downloaded. This includes any NA-only (ie. empty) columns where they occur.
 * This package only downloads timeseries data tables. Other data tables (for example,
   pivot tables) are ignored.
 * The index for all of the downloaded tables should be a pandas PeriodIndex, with an
   appropriately selected frequency. 
 * In the process of data retrieval, the ABS data tables are downloaded and stored in a 
   local cache. By default the cache directory is "./.readabs_cache/". 
   You can change the default directory name by setting the environemnt variable 
   "READABS_CACHE_DIR" with the name of the preferred directory.
 * the "read" functions have a number of standard keyword arguments (with default 
   settings as follows):
   - `history=""` - provide a month-year string to extract historical ABS data.  
     For example, you can set history="dec-2023" to the get the ABS data for a 
     catalogue identifier that was originally published in respect of Q4 of 2023. 
     Note: not all ABS data sources are structured so that this technique works
     in every case; but most are.
   - `verbose=False` - Do not print detailed information on the data retrieval process.
     Setting this to true may help diagnose why something might be going wrong with the
     data retrieval process. 
   - `ignore_errors=False` - Cease downloading when an error in encounted. However,
     sometimes the ABS website has malformed links, and changing this setting is 
     necessitated. (Note: if you drop a message to the ABS, they will usually fix 
     broken links with a business day). 
   - `get_zip=True` - Download .zip files. 
   - `get_excel_if_no_zip=True` Only try to download .xlsx files if there are no
     zip files available to be downloaded.
   - `get_excel=False` - Do not automatically download .xlsx files. 
     Note at least one of get_zip, get_excel_if_no_zip, or get_excel must be true. 
     For most ABS catalogue items, it is sufficient to just download the one zip 
     file. But note, some catalogue items do not have a zip file. Others have 
     quite a number of zip files.
  - `single_excel_only=""` - if this argument is set to a table name (without the 
    ,xlsx extention), only that excel file will be downloaded. If set, and only a 
    limited subset of available data is needed, this can speed up download 
    times significantly. Note: overrides get_zip, get_excel_if_no_zip, get_excel and 
    single_zip_only.
 - `single_zip_only=""` - if this argument is set to a zip file name (without
   the .zip extention), only that zip file will be downloaded. If set, and only a 
   limited subset of available data is needed, this can speed up download times 
   significantly. Note: overrides get_zip, get_excel_if_no_zip, and get_excel.

