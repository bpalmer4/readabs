# readabs

Description
-----------
Readabs is an open-source python package to download and work with 
timeseries data from the Australian Bureau of Statistics (ABS) and
the Reserve Bank of Australia (RBA), using pandas DataFrames. 

Quick overview of the key functions:

ABS
---
- abs_catalogue() - returns a pandas DataFrame of ABS catalogue numbers.
   Note: typically, an ABS Catalogue item comprises multiple data tables.
- read_abs_cat() - returns a tuple containing the complete ABS Catalogue
    information as a python dictionary of pandas DataFrames (one for each 
    table in the catalogie), as well as the associated metadata in a
    separate DataFrame.
- read_abs_series() - get one or more series for a specified catalogue
    number and the specified series identifier(s). Returns a tuple of 
    two DataFrames, one for the primary data and one for the metadata.
- read_abs_by_desc() - get one or more series, for a specified catalogue
    number, based on searching for matching data item descriptions. Returns
    a tuplwe of (1) a dictionary with the series name as the key and the 
    pandas series as the value and (2) a dataframe of meta data
- search_abs_meta() - searchs the abs meta data for 1 or more rows that 
    match the desired search-terms. Returns the matching rows from the 
    meta data
- find_abs_id() - search the abs metadata for the one specific series
    that matches the search terms. Returns a tuple of the table name, 
    series_id and units for the unique series_id that matches the search-
    terms.

RBA
---
- rba_catalogue - returns a pandas DataFrame of RBA catalogue numbers.
    Note: whereas multiple data tables are associated with an ABS 
    catalogue number, onle a single table is associated with an RBA 
    catalogue number.
- read_rba_table() - read a table from the RBA website and return the 
    actual data and the meta data in a tuple of two DataFrames.


For more information
--------------------
For complete details, refer to the API usage documents in the ./docs 
directory.

---
