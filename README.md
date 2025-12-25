# readabs

A Python package for downloading and working with timeseries data from the Australian Bureau of Statistics (ABS) and Reserve Bank of Australia (RBA).

## Overview

**readabs** automates the retrieval of ABS and RBA Excel spreadsheets from their websites, caches them locally, and provides a clean pandas DataFrame interface for analysis. Instead of manually downloading spreadsheets, navigating complex Excel files, and writing parsing code, readabs handles all of this automatically.

The ABS publishes timeseries data as Excel files with a specific structure: "Data" sheets contain the actual values, while "Index" sheets contain metadata describing each series. readabs parses both, giving you clean DataFrames with proper time indices and full metadata for every series.

### Key Features

- **Automatic downloading**: Fetches Excel/ZIP files directly from ABS and RBA websites
- **Smart caching**: Caches downloaded files locally and only re-downloads when data is updated
- **Clean DataFrame output**: Returns timeseries as pandas DataFrames with proper PeriodIndex
- **Metadata preservation**: Retains full ABS/RBA metadata (series descriptions, units, frequency)
- **Flexible retrieval**: Get entire catalogues, specific series by ID, or search by description
- **Time series utilities**: Built-in functions for frequency conversion, percentage changes, and unit scaling

## Installation

```bash
pip install readabs
```

Or using [uv](https://docs.astral.sh/uv/):

```bash
uv add readabs
```

## Quick Start

```python
import readabs as ra
from readabs import metacol as mc  # ABS metadata column names

# Download the complete Labour Force Survey (ABS 6202.0)
data, meta = ra.read_abs_cat("6202.0")

# data is a dict of DataFrames (one per table)
# meta is a DataFrame containing all series metadata

# Access a specific table
labour_force = data["6202001"]
print(labour_force.head())
```

## Usage Examples

### Browse Available Data

```python
# List all available ABS catalogues
ra.print_abs_catalogue()

# List all RBA tables
ra.print_rba_catalogue()
```

Note: The ABS catalogue includes discontinued series marked as "CEASED". These may still be accessible using the `url` parameter (see "Historical and Archived Data" below).

### Get Specific Series by ID

```python
# Get unemployment rate series by its Series ID
unemployment, meta = ra.read_abs_series(
    cat="6202.0",
    series_id="A84423050A"
)
```

### Search for Data by Description

```python
# Find and retrieve series by searching metadata
search_terms = {
    "Unemployment rate": mc.did,       # Data Item Description
    "Persons": mc.did,
    "Seasonally Adjusted": mc.stype,   # Series Type
}
results = ra.search_abs_meta(meta, search_terms)

# Or retrieve directly using read_abs_by_desc()
wanted = {
    "Unemployment Rate": {
        "cat": "6202.0",
        "did": "Unemployment rate ;  Persons ;",
        "stype": "Seasonally Adjusted",
    },
}
series_dict, meta = ra.read_abs_by_desc(wanted)
```

### RBA Data

```python
# Get the Official Cash Rate
ocr = ra.read_rba_ocr(monthly=True)

# Read any RBA table
rba_data, rba_meta = ra.read_rba_table("A1")

# Historical RBA tables are prefixed with "Z:"
hist_data, hist_meta = ra.read_rba_table("Z:A1")
```

Use `print_rba_catalogue()` to see all available tables, including historical ones.

### Historical and Archived Data

For older data no longer in the current ABS catalogue, you can work with local ZIP files or specific URLs:

```python
# Parse a previously downloaded ABS ZIP file
data_dict = ra.grab_abs_zip("/path/to/downloaded/abs_data.zip")

# Fetch data from a specific ABS URL (useful for archived pages)
data_dict = ra.grab_abs_url(url="https://www.abs.gov.au/some/archived/page")

# Access historical releases using the history parameter
data, meta = ra.read_abs_cat("6202.0", history="dec-2023")

# Or use a direct URL with read_abs_cat
data, meta = ra.read_abs_cat(url="https://www.abs.gov.au/statistics/...")
```

These functions return a dictionary of DataFrames (one per Excel sheet), allowing you to work with data that may have been removed from the main ABS catalogue.

### Advanced Options

The `read_abs_cat()` function accepts several optional parameters for fine-tuning:

```python
data, meta = ra.read_abs_cat(
    "6202.0",
    single_excel_only="6202001",  # Only download one specific table (faster)
    cache_only=True,              # Use cached data only (offline mode)
    verbose=True,                 # Print diagnostic messages
    ignore_errors=True,           # Continue if some files fail to download
    keep_non_ts=True,             # Include non-timeseries tables in output
)
```

| Parameter | Description |
|-----------|-------------|
| `single_excel_only` | Download only the specified Excel file (e.g., "6202001") |
| `single_zip_only` | Download only the specified ZIP file |
| `cache_only` | Only use locally cached files, don't download |
| `verbose` | Print progress and diagnostic information |
| `ignore_errors` | Continue processing if some downloads fail |
| `keep_non_ts` | Include non-timeseries tables in the output |

### Time Series Utilities

```python
# Calculate percentage change
annual_growth = ra.percent_change(quarterly_data, n_periods=4)

# Convert quarterly to monthly (with interpolation)
monthly = ra.qtly_to_monthly(quarterly_data, interpolate=True)

# Convert monthly to quarterly
quarterly = ra.monthly_to_qtly(monthly_data, q_ending="DEC", f="mean")

# Scale large numbers and adjust unit labels
scaled_data, new_units = ra.recalibrate(data, "Number")
# e.g., 1,500,000 "Number" becomes 1.5 "Million"
```

## API Reference

### ABS Functions

| Function | Description |
|----------|-------------|
| `read_abs_cat(cat)` | Download complete ABS catalogue as dict of DataFrames + metadata |
| `read_abs_series(cat, series_id)` | Get specific series by Series ID |
| `read_abs_by_desc(wanted)` | Get series by searching descriptions |
| `abs_catalogue()` | Get DataFrame of all ABS catalogue numbers |
| `print_abs_catalogue()` | Print formatted table of ABS catalogues |
| `search_abs_meta(meta, terms)` | Search metadata for matching series |
| `find_abs_id(meta, terms)` | Find unique series matching search terms |
| `grab_abs_url(url)` | Fetch data from a specific ABS URL |
| `grab_abs_zip(zip_path)` | Parse a local ABS ZIP file |

### RBA Functions

| Function | Description |
|----------|-------------|
| `read_rba_table(table)` | Read RBA table, returns data + metadata |
| `read_rba_ocr(monthly=True)` | Get Official Cash Rate as Series |
| `rba_catalogue()` | Get DataFrame of RBA table numbers |
| `print_rba_catalogue()` | Print formatted table of RBA catalogues |

### Utility Functions

| Function | Description |
|----------|-------------|
| `percent_change(data, n)` | Calculate percentage change over n periods |
| `annualise_rates(data, periods)` | Convert rates to annualized values |
| `annualise_percentages(data, periods)` | Convert percentages to annualized values |
| `qtly_to_monthly(data)` | Convert quarterly to monthly frequency |
| `monthly_to_qtly(data)` | Convert monthly to quarterly frequency |
| `recalibrate(data, units)` | Scale values and adjust unit labels |

### Metadata Constants

```python
from readabs import metacol as mc   # ABS metadata columns
from readabs import rba_metacol as rm  # RBA metadata columns

# ABS metadata columns include:
# mc.did   - Data Item Description
# mc.id    - Series ID
# mc.unit  - Unit (e.g., "Percent", "Number")
# mc.freq  - Frequency
# mc.stype - Series Type (e.g., "Seasonally Adjusted")
# mc.table - Table name
```

## Caching

Downloaded files are cached locally to avoid repeated downloads. The cache location can be configured:

```python
# Default: ./.readabs_cache/ in the current directory
# Override with environment variable:
import os
os.environ["READABS_CACHE_DIR"] = "/path/to/cache"
```

The cache respects HTTP `Last-Modified` headers, so data is only re-downloaded when the source files have been updated.

## Return Types

Most ABS functions return a tuple:
- `read_abs_cat()`: `tuple[dict[str, DataFrame], DataFrame]` - dict of data tables + metadata
- `read_abs_series()`: `tuple[DataFrame, DataFrame]` - data + metadata
- `read_abs_by_desc()`: `tuple[dict[str, Series], DataFrame]` - named series + metadata

DataFrames use pandas `PeriodIndex` with appropriate frequency (Monthly, Quarterly, Yearly).

## Documentation

Full API documentation is available in the `./docs` directory. Generate updated documentation with:

```bash
pdoc ./src/readabs -o ./docs
```

Or view the generated HTML documentation in your browser.

## Requirements

- Python 3.11+
- pandas, numpy, requests, beautifulsoup4, lxml, openpyxl, pyxlsb

## License

This project is open source. See the repository for license details.

## Links

- **Repository**: https://github.com/bpalmer4/readabs
- **PyPI**: https://pypi.org/project/readabs/
