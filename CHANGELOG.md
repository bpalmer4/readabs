Version 0.0.16 released X (Canberra, Australia)

- Major changes
   * removed the old-docs directory.

- Minor changes
   *

---

Version 0.0.15 released 25-Jul-2024 (Canberra, Australia)

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
