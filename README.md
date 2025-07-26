readabs
=======

Description
-----------
Readabs is an open-source Python package to download and work with 
timeseries data from the Australian Bureau of Statistics (ABS) and
the Reserve Bank of Australia (RBA), using pandas DataFrames. 

Import
------
```python
import readabs as ra
from readabs import metacol as mc  # column names for ABS metadata
from readabs import rba_metacol as rm  # column names for RBA metadata
```

ABS Functions
-------------
- `abs_catalogue()` - returns a pandas DataFrame of ABS catalogue numbers.
   Note: typically, an ABS Catalogue item comprises multiple data tables.
- `print_abs_catalogue()` - prints a formatted table of ABS catalogue numbers.
- `read_abs_cat()` - returns a tuple containing the complete ABS Catalogue
    information as a python dictionary of pandas DataFrames (one for each 
    table in the catalogue), as well as the associated metadata in a
    separate DataFrame.
- `read_abs_series()` - get one or more series for a specified catalogue
    and the specified series identifier(s). Returns a tuple of 
    two DataFrames, one for the primary data and one for the metadata.
- `read_abs_by_desc()` - get one or more series, for a specified catalogue
    number, based on searching for matching data item descriptions. Returns
    a tuple of (1) a dictionary with the series name as the key and the 
    pandas Series as the value and (2) a DataFrame of metadata.
- `search_abs_meta()` - searches the ABS metadata for 1 or more rows that 
    match the desired search-terms. Returns the matching rows from the 
    metadata.
- `find_abs_id()` - search the ABS metadata for the unique series
    that matches the search terms. Returns a tuple of the table name,
    series_id and units for the series_id that matches the search
    terms. Raises an exception if no items, or more than one item in
    the metadata matches the search terms.

RBA Functions
-------------
- `rba_catalogue()` - returns a pandas DataFrame of RBA catalogue numbers.
    Note: whereas multiple data tables are associated with an ABS 
    catalogue number, only a single table is associated with an RBA 
    catalogue number.
- `print_rba_catalogue()` - prints a formatted table of RBA catalogue numbers.
- `read_rba_table()` - read a table from the RBA website and return the 
    actual data and the metadata in a tuple of two DataFrames.
- `read_rba_ocr()` - read the Official Cash Rate (OCR) from the RBA website.
    Returns a pandas Series with either daily or monthly frequency.

Utility Functions
-----------------
- `recalibrate()` - returns a pandas Series/DataFrame where the units have
    been scaled to be less than 1,000. Also adjusts the units label.
- `recalibrate_value()` - recalibrate a single numeric value.
- `percent_change()` - calculate percentage change for time series data.
- `annualise_rates()` - convert rates to annualized values.
- `annualise_percentages()` - convert percentages to annualized values.
- `qtly_to_monthly()` - convert quarterly data to monthly frequency.
- `monthly_to_qtly()` - convert monthly data to quarterly frequency.

Data Types and Metadata
-----------------------
- `Datatype` - enumeration for ABS data types.
- `ReadArgs` - TypedDict for keyword arguments used by ABS reading functions.
- `metacol` - column names for ABS metadata.
- `rba_metacol` - column names for RBA metadata.

For more information
--------------------
For complete details, refer to the API documentation in the ./docs 
directory, or visit the generated HTML documentation.

---
