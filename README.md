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
labour_force = data["62020001"]
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

By default, search terms are matched as substrings (via `.str.contains()`), so a partial description like `"Unemployment rate ;  Persons ;"` will match the full `"Unemployment rate ;  Persons ;  Australia ;"`. Pass `exact_match=True` to `search_abs_meta()` to require an exact (`==`) match instead.

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

# Or fetch a discontinued series by URL (the catalogue number is still required)
data, meta = ra.read_abs_cat("8501.0", url="https://www.abs.gov.au/statistics/...")
```

These functions return a dictionary of DataFrames (one per Excel sheet), allowing you to work with data that may have been removed from the main ABS catalogue.

### Advanced Options

The `read_abs_cat()` function accepts several optional parameters for fine-tuning:

```python
data, meta = ra.read_abs_cat(
    "6202.0",
    single_excel_only="62020001",  # Only download one specific table (faster)
    cache_only=True,              # Use cached data only (offline mode)
    verbose=True,                 # Print diagnostic messages
    ignore_errors=True,           # Continue if some files fail to download
    keep_non_ts=True,             # Include non-timeseries tables in output
)

# Or download a chosen subset of tables (skips the full-catalogue zip):
data, meta = ra.read_abs_cat(
    "6202.0",
    selected_excel=("62020001", "62020017", "62020X28"),
)
```

| Parameter | Description |
|-----------|-------------|
| `single_excel_only` | Download only the specified Excel file (e.g., "62020001") |
| `selected_excel` | Tuple of Excel file names to download (e.g., `("62020001", "62020017")`). Must be a tuple, not a list. |
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

### Splicing Series (mixed frequency / multiple vintages)

Many ABS concepts are spread across frequencies and releases — e.g. a *monthly*
CPI that only reaches back to 2017, a *quarterly* one back to 1948, and a
discontinued monthly indicator covering the gap between. `splice` joins such
segments into one continuous series, **highest priority first**: it prefers the
higher-priority value where periods overlap and leaves honest gaps where no
source has data (no interpolation, nothing invented). Pass `rebase=True` to
*multiplicatively* rescale segments whose levels differ (e.g. an index
reference-period change) onto the running result — it is off by default, because
rebasing transforms your data and is only valid for ratio-scale (index-like)
series. A join report records every rebase factor and overlap so a splice can be
audited rather than trusted blindly.

Four composable functions:

| Function | Role |
|----------|------|
| `select_one(data, meta, selector)` | Select one series from fetched `(data, meta)` (ABS unit kept on `.attrs["unit"]`) |
| `select(sources)` | Iterable of `(data, meta, selector)` → list of series; raises on mixed units (opt out with `require_same_units=False`) |
| `splice(segments)` | Splice an iterable of series, highest priority first → `(series, report)` |
| `select_and_splice(sources)` | `select` then `splice` for the no-transform case; checks units → `(series, unit, report)` |

A *selector* is either the `{search_value: column}` form used by `find_abs_id`
(with `validate_unique=True`, so it de-duplicates on Series ID and raises on
genuine ambiguity rather than guessing), **or a bare ABS Series ID string**
(e.g. `"A2325846C"`, matched exactly) for when you already know precisely which
series you want. The two forms mix freely across sources:

```python
series, unit, report = ra.select_and_splice([
    (cur, cmeta, base | {"Month": mc.freq}),   # by description
    (cur, cmeta, "A2325846C"),                 # by Series ID (quarterly All groups CPI)
], rebase=True)
```

By default `select` **raises if the selected series carry different ABS units** —
coherence is required to splice. Pass `require_same_units=False` to select
different-unit series on purpose (as the unemployment example below does).

**No per-series transform — splice index levels with `rebase=True`** (headline
CPI index: new monthly over the discontinued indicator over the long quarterly,
rescaled across reference-period changes):

```python
cur, cmeta = ra.read_abs_cat("6401.0")                       # monthly + long quarterly
ind, imeta = ra.read_abs_cat("6484.0", url=INDICATOR_URL)    # discontinued -> fetch by URL

base = {"Index Numbers ;  All groups CPI ;  Australia ;": mc.did, "Index Numbers": mc.unit}
series, unit, report = ra.select_and_splice(
    [
        (cur, cmeta, base | {"Month": mc.freq}),     # new monthly CPI  (2024 ->)
        (ind, imeta, base | {"Month": mc.freq}),     # monthly indicator (2017-2025)
        (cur, cmeta, base | {"Quarter": mc.freq}),   # quarterly back to 1948
    ],
    output="M",
    rebase=True,   # index reference-period change -> rescale onto the running result
)
```

The shared `base` selector resolves the same concept in all three sources; only
the frequency override changes. `rebase=True` is needed because these index
segments sit on different reference periods — for series that already share a
level (or aren't ratio-scale), leave it off.

**With a transform — select, transform each, then splice** (year-ended inflation:
a Y/Y change is base-invariant, so compute it per source and splice the *rates*
with `rebase=False`):

```python
m_idx, i_idx, q_idx = ra.select([
    (cur, cmeta, base | {"Month": mc.freq}),
    (ind, imeta, base | {"Month": mc.freq}),
    (cur, cmeta, base | {"Quarter": mc.freq}),
])

def yoy(s, periods):
    return ((s / s.shift(periods) - 1) * 100).dropna()

long_yoy, report = ra.splice(
    [yoy(m_idx, 12), yoy(i_idx, 12), yoy(q_idx, 4)],
    rebase=False,   # rates are comparable: coalesce, never rescale
)
```

**A transform across two series** (unemployment rate back to 1959): the
modellers' database (1364.0.15.003) publishes *unemployed* and *labour force* but
not the rate, while the Labour Force Survey publishes the monthly rate directly —
so compute the quarterly rate, then splice it under the monthly one:

```python
md,  mmeta = ra.read_abs_cat("1364.0.15.003", single_excel_only="1364015003")
lfs, lmeta = ra.read_abs_cat("6202.0", single_excel_only="62020001")

# Two counts ("000") and a rate ("Percent") in one select -> the units differ on
# purpose, so switch the coherence check off (select raises on mixed units by default):
unemployed, labour_force, ur_monthly = ra.select([
    (md,  mmeta, {"1364015003": mc.table, "Total unemployed ;": mc.did}),    # "000"
    (md,  mmeta, {"1364015003": mc.table, "Total labour force ;": mc.did}),  # "000"
    (lfs, lmeta, {"62020001": mc.table, "Unemployment rate ;  Persons ;": mc.did,
                  "Seasonally Adjusted": mc.stype}),                         # "Percent"
], require_same_units=False)

ur_quarterly = unemployed / labour_force * 100        # the rate the source withholds
ur, report = ra.splice([ur_monthly, ur_quarterly], rebase=False)   # monthly priority, 1959 ->
```

`splice` is source-agnostic — hand it any series you've already fetched:

```python
out, report = ra.splice([monthly_series, quarterly_series], rebase=False)
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

### Splicing Functions

| Function | Description |
|----------|-------------|
| `select_one(data, meta, selector)` | Select one series from fetched `(data, meta)` |
| `select(sources)` | Iterable of `(data, meta, selector)` → list of series |
| `splice(segments)` | Splice an iterable of series, highest priority first |
| `select_and_splice(sources)` | Select + splice (no-transform case); checks units |

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

## How readabs gets data (and why it can occasionally break)

There is no official, stable ABS API that exposes the full time series
collection. The ABS publishes its data as Excel/zip files linked from
statistics landing pages, following conventions that are consistent but
undocumented: predictable file names, an `Index` sheet carrying the metadata,
and `{table}---{sheet}` sheet naming. readabs works by following those
conventions — it fetches the landing page, finds the spreadsheet links,
downloads them, and parses the sheets.

This means readabs depends on ABS *practice*, not a contract. When the ABS
renames a table, restructures a page, or discontinues a series, a call may
fail or return less than expected — not because of a bug here, but because the
upstream habit changed. readabs is built to fail loudly when this happens, and
it caches downloads so transient outages don't block you. If something stops
working, check whether the ABS has changed that release, and use the `url=` and
`history=` parameters to reach archived data.

The ABS does run an SDMX/REST data API at `data.api.abs.gov.au`. As of 2025 the
ABS describes it as *beta*: it carries only a subset of what's published on the
ABS website (some dataflows are not uploaded at all), it lags the website
release, and it has no mechanism for retrieving earlier vintages of a revised
series. For the data it does cover, a companion package —
[`sdmxabs`](https://github.com/bpalmer4/sdmxabs) — wraps that API directly.
readabs instead targets the published spreadsheets, which remain the most
complete source and (via `history=`) allow access to earlier vintages.

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
- **sdmxabs** (companion package for the ABS SDMX/REST data API): https://github.com/bpalmer4/sdmxabs
- **readabs for R** (a separate, like-named ABS package by Matt Cowgill): https://github.com/mattcowgill/readabs
