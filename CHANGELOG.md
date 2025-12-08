Version 0.1.8 released 08-Dec-2025 (Canberra Australia)

 - Added `url` parameter to `read_abs_cat()` for retrieving discontinued ABS series
   that are no longer in the ABS Time Series Directory. Example usage:
   `read_abs_cat(cat="8501.0", url="https://www.abs.gov.au/.../jun-2025")`
 - Improved error message when catalogue number not found - now suggests using
   the `url` parameter as an alternative
 - Fixed linter issues (import sorting, unused variable output)

---

Version 0.1.7 released 28-Nov-2025 (Canberra Australia)

 - fixed a glitch when all columns are NA in a dataframe.

---

Version 0.1.6 released 27-Nov-2025 (Canberra Australia)

 - fixed a glitch in 0.1.5 - grab_abs_zip() was not properly exposed

---
Version 0.1.5 released 26-Nov-2025 (Canberra Australia)

 - exploring the ability to load ABS zip files on the local file system directly
 - one new API function: grab_abs_zip() - a primative, which most wont use
 - new argument to read_abs_cat(): zip_file: str | Path = "" - if this is set to a 
   file name then this function will extract data from that zip file on the local 
   file system. This may be useful for debugging purposes.
 - this should be treated as test code (use at your own risk)

---

Version 0.1.4 released 26-Jul-2025 (Canberra Australia)

- Improved type hints with `ReadArgs` TypedDict for better IDE support
- Added `keep_non_ts` parameter to type definitions
- Exposed `ReadArgs` in public API
- Fixed all mypy/pyright type checking errors

---

Version 0.1.3 released 25-Jul-2025 (Canberra Australia)

- Atomic cache file replacement, better exception handling, code cleanup
- Python requirement: >=3.12 → >=3.11

---

Version 0.1.2 released 20-Jul-2025 (Canberra Australia)

- Bug fixes and improvements
    * Enhanced exception handling in grab_abs_url.py when converting raw bytes to ExcelFile
    * Added pyxlsb dependency to support reading xlsb format Excel files

- Development improvements
    * Added .pylintrc configuration file with max-line-length set to 120
    * Added uv-upgrade.sh script for upgrading dependencies

- Version updates
    * Bumped version to 0.1.2 in pyproject.toml

---

Version 0.1.1 released 19-Jul-2025 (Canberra Australia)

- Code quality improvements
    * Comprehensive code review and linting improvements across all files
    * Fixed type annotations and docstring formatting throughout the package
    * Added per-file exclusions in pyproject.toml for legitimate ANN401 cases
    * Improved error handling and constants for magic numbers
    * Fixed pandas regex warning in abs_catalogue.py by removing parentheses from CEASED_MARKER

- Documentation updates
    * Updated README.md to accurately reflect all available functions and improved formatting
    * Added missing functions (print_abs_catalogue, print_rba_catalogue, read_rba_ocr, etc.)
    * Improved code examples and formatting

---

Version 0.0.32 released 03-Jul-2025 (Canberra Australia)

- minor changes
    * ABS has changed a column label from "Catalogue Number"
      to "Catalogue number"
    * minor clean up.

---

Version 0.0.31 released 04-Jun-2025 (Canberra Australia)

- Minor changes
  * Today's national accounts included a bunch of 
    "Mock-up" links and zipfiles. As a tempory fix, I ignore
    URLs with the string "Mock-up" in them.

---

Version 0.0.30 released 02-Jun-2025 (Canberra Australia)

- Minor changes
  * updated build-test.sh, pyproject.toml and __init__.py,
    to further integrate the use of uv

---

Version 0.0.29 released 24-May-2025 (Canberra Australia)

- Minor changes
  * glitch with previous upload

---

Version 0.0.28 released 24-May-2025 (Canberra Australia)

- Minor changes
  * added tabulate to the package requirements

---

Version 0.0.27 released 10-May-2025 (Canberra Australia)

- Minor changes
  * using uv to build the package

---

Version 0.0.26 released 31-Jan-2025 (Canberra, Australia)

- Minor changes
   * updates to getting a single excel file only

---

Version 0.0.25 released 25-JAN-2025 (Canberra, Australia)

- Minor changes
   * updates to grab_abs_url - additional print statements
     if in verbose mode.

---

Version 0.0.24 released 10-JAN-2025

- Minor changes
   * Updates to the README.md file
   * Updates to the pdoc build_docs.sh file

---

Vwesion 0.0.23 released 10-JAN-2025 (Canberra, Australia)

- Minor changes
   * updated scripts so that the pdoc system updates the
     documentation 

---

Version 0.0.22 released 10-JAN-2025 (Canberra, Australia)

- Minor changes
   * Added ruff to the linting regimen
   * Updated the README.md file

---

Version 0.0.21 released 09-JAN-2025 (Canberra, Australia)

- Major changes
   * Added a new function to get one or more ABS series by
     seraching for data item descriptions: read_abs_by_desc().

- Minor changes
   * Updated the README.md file

---

Version 0.0.20 released 04-JAN-2025 (Canberra, Australia)

- Minor changes
   * read_rba_table() can now read historical tables that use
     "Mnemonic" rather than "Series-ID" as the name for 
     the data items in the table. 
   * Some historical tables are not in a form that can be easily
     parsed in a manner similar to the current RBA data. These
     tables have been excluded from the historic catalogue:
     ("E4", "E5", "E6", "E7", "J1", "J2", "Occassional Papers")

---

Version 0.0.19 released 03-JAN-2025 (Canberra, Australia)

- Major changes
   * the RBA Historical Data files are now included in the RBA
     catalogue. The table names all begin with "Z:". I have not
     fully tested this addition. 

---

Version 0.0.18 released 02-JAN-2025 (Canberra, Australia)

- Minor changes
   * read_rba_table() fixed to get adjust for a malformed link on
     the RBA website, which affected the F1 table.

---

Version 0.0.17 released 31-JUL-2024 (Canberra, Australia)

- Minor changes
   * largely tidy-ups.

---

Version 0.0.16 released 26-JUL-2024 (Canberra, Australia)

- Major changes
   * removed the old-docs directory.
   * Finished documenting the API, using pdoc3

- Minor changes
   * Some code reorganisation

---

Version 0.0.15 released 25-JUL-2024 (Canberra, Australia)

- Major changes
   * Removed the incomplete documentation from the 
     'README.md' file.
   * Worked out the proper import arrangements. Removed the
     'readabs.py' file. Expanded '__init__.py'
   * Removed the generate_catalogue_map.py and rewrote the 
     abs_catalogue.py to dunamically download the catalogue.
   * Started using pdoc3 to automate the generation of API
     documents. API comments are a work in progress, and
     there is no guarantee I will stick with pdoc3. 

- Minor changes
   * Added __all__ to __init__.py, to allow for wildcard 
     imports
   * Applied mypy and pylint to the package. Down to zero 
     mypy issues and one pylint issue. 
---

Version 0.0.14 released 21-JUL-2024 (Canberra, Australia)

- Major changes
   * put the recalibrate() function into its own module.
     Added some in-module tests.
   * Removed the ./tests directory. In the interim, I have 
     been placeing quick code-tests inline. Will need to 
     more sensibly revisit code testing in the future. 
---

Version 0.0.13 released 19-JUL-2024 (Canberra, Australia)

- Minor changes
   * Further code tidy-ups
   * tidy-ups to read_rba_ocr() in read_rba_table.py
   * removed a print statment from get_rba_links.py
---

Version 0.0.12 released 17-JUL-2024 (Canberra, Australia)

- Major changes
   * Completed initial work to read in data files from the 
     Reserve Bank of Australia (RBA). This will need work 
     over the next few days.
---

Version 0.0.11 released 17-JUL-2024 (Canberra, Australia)

- Minor changes
   * Largely bug fixes and code tidy-ups.
   * Ignore excel files that cannot be parsed into a DataFrame
   * Only delete empty rows after tables have been combined
---

Version 0.0.10 - released 16-JUL-2024 (Canberra, Australia)

- Major changes
   * Working towards functions that will also capture data from
     the Reserve Bank of Australia. As a first step:
     - Renamed a number of functions to make it clear they are 
       working with ABS data (and not data generally).
     - Added functions to print_rba_catalogue() and get the 
       rba_catalogue()

- Minor changes
   * Some files have been renamed. 
   * Updates to README.md
---

Version 0.0.9 - released 14-JUL_2024 (Canberra, Australia)

- Minor changes
   * Largely bug fixes and code tidy-ups. Some files have been
     renamed.
---

Version 0.0.8 - released 13-JUL-2024 (Canberra, Australia)

- Major changes
   * Rewrote 'read_abs_cat.py' and created 'grab_abs_url.py' to
     separate the ABS table capture code from the timeseries 
     compilation code. Also, it is now possible to capture non-
     timeseries data from the ABS. 
---

Version 0.0.7 - released 8-JUL-2024 (Canberra, Australia)

- Minor changes
   * fixed a bug in monthly_to_qtly() in 'src/readabs/utilities.py'
---

Version 0.0.6 - released 07-JUL-2024 (Canberra, Australia)

- Major changes
   * Changes to allow for typing information 

- Minor changes
   * Updated the README.md file.
   * Minor change to the unit recalibrate() utility
   * Updated version number in '__init__.py'
---

Version 0.0.5 - released 30-JUN-2024 (Canberra, Australia)

- Major changes:
   * added search_meta() and find_id() functions, to allow for 
     the selection of data item series_IDs, based on search-terms 
     over the meta data. 
   * added a cache_only flag to read_abs_cat() and read_abs_series(),
     allowing for offline coding/testing.

- Minor changes:
   * Minor edits to the README.md file.
   * Added a module comment to 'get_data_links.py'
   * Corrected a typo in the module comment for 'generate_catalogue_map.py'
   * changed the m_periods parameter in percent_change() to n_periods
   * added this change log 
   * Updated version number in '__init__.py'
___
