# readabs

readabs is an open-source python package to download timeseries data from
the Australian Bureau of Statistics (ABS) into a pandas DataFrame.

## Notes:

 * ABS data tables are downloaded and stored in a cache. By default the cache
   directory is ./.readabs" You can change the default directory name ny setting
   the environemnt variable "READABS_CACHE_DIR" with the name of the directory.

