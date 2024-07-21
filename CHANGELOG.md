Version 0.0.14 released X )Canberra, Australia)

- Major changes
   * put the recalibrate() function into its own module.
     Added some in-module tests.
   * Removed the ./tests directory. In the interim, I have 
     been placeing quick code-tests inline. Will need to 
     more sensibly revisit code testing in the future. 
   * Moved generate_catalogue_map.py to the main directory, 
     as it is not part of the package. We are now keeping
     old catalogue map files; just in case the ABS removes
     the catalogue directory webpage I have been using.  
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
