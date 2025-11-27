"""Quick and dirty test code."""

import readabs as ra

def clean_diagnostic_test():
    """
    A simple, untweaked script to demonstrate the raw error from readabs.
    This script contains no error handling and is expected to crash.
    """

    catalogues_to_test = {
        #'3401.0': 'Overseas Migration',
        '6401.0': 'Consumer Price Index, Australia',
        #'6202.0': 'Labour Force, Australia',
        #'5206.0': 'Australian National Accounts'
    }

    for cat_id, description in catalogues_to_test.items():
        print(f"Attempting to call ra.read_abs_cat() for: {cat_id} ({description})")
        _data_tables, _metadata = ra.read_abs_cat(cat_id)
        print(f"Success for {cat_id}")

    zip_test = "../src/readabs/.test-data/Qrtly-CPI-Time-series-spreadsheets-all.zip"
    print(f"Attempting to call ra.read_abs_cat() for local zip file: {zip_test}")
    _data_tables, _metadata = ra.read_abs_cat(cat="", zip_file = zip_test)
    print("Success for local zip file")

if __name__ == "__main__":
    clean_diagnostic_test()
