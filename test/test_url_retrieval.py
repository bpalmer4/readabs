"""Test retrieving data using a direct URL for discontinued series."""

import readabs as ra


def test_discontinued_retail_sales():
    """
    Test retrieving the discontinued Retail Trade series (8501.0) using a direct URL.
    This series was discontinued after June 2025 and is no longer in the ABS Time Series Directory.
    """

    # The Retail Trade Australia page - last release June 2025
    url = "https://www.abs.gov.au/statistics/industry/retail-and-wholesale-trade/retail-trade-australia/jun-2025"

    print(f"Attempting to retrieve discontinued series via URL: {url}")

    # Using read_abs_cat with url parameter (cat can be empty or descriptive)
    data_tables, metadata = ra.read_abs_cat(cat="8501.0", url=url)

    print(f"Success! Retrieved {len(data_tables)} tables")
    print(f"Tables: {list(data_tables.keys())}")
    print(f"Metadata shape: {metadata.shape}")

    for table_name, df in data_tables.items():
        freq_str = getattr(df.index, "freqstr", "Unknown")
        print(f"  {table_name}: {df.shape}, freq={freq_str}")


if __name__ == "__main__":
    test_discontinued_retail_sales()
