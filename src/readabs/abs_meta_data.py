"""Support for working with ABS metadata."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Metacol:
    """Column names for ABS metadata DataFrames.

    A frozen dataclass that holds standardized column names used in
    ABS metadata. The frozen property ensures immutability of the
    column name mappings.
    """

    did: str = "Data Item Description"
    stype: str = "Series Type"
    id: str = "Series ID"
    start: str = "Series Start"
    end: str = "Series End"
    num: str = "No. Obs."
    unit: str = "Unit"
    dtype: str = "Data Type"
    freq: str = "Freq."
    cmonth: str = "Collection Month"
    table: str = "Table"
    tdesc: str = "Table Description"
    cat: str = "Catalogue number"


# Global instance for consistent access to column names
metacol = Metacol()
"""Pre-instantiated Metacol object for accessing ABS metadata column names.

This frozen dataclass instance provides consistent access to standardized
column names used in ABS metadata DataFrames. Its attributes cannot be
modified after creation, ensuring data integrity.

Example:
    >>> metacol.did
    'Data Item Description'
    >>> metacol.id
    'Series ID'
"""


# --- testing
if __name__ == "__main__":

    def test_metacol() -> None:
        """Test the Metacol dataclass functionality.

        Verifies that all column name attributes are accessible and that
        the frozen dataclass properly prevents modification and deletion.
        """
        # Test all column name attributes
        print("Column names:")
        print(f"  Data Item Description: {metacol.did}")
        print(f"  Series Type: {metacol.stype}")
        print(f"  Series ID: {metacol.id}")
        print(f"  Series Start: {metacol.start}")
        print(f"  Series End: {metacol.end}")
        print(f"  Number of Observations: {metacol.num}")
        print(f"  Unit: {metacol.unit}")
        print(f"  Data Type: {metacol.dtype}")
        print(f"  Frequency: {metacol.freq}")
        print(f"  Collection Month: {metacol.cmonth}")
        print(f"  Table: {metacol.table}")
        print(f"  Table Description: {metacol.tdesc}")
        print(f"  Catalogue Number: {metacol.cat}")

        print("\nTesting immutability:")

        # Test access to non-existent attribute
        try:
            print(metacol.does_not_exist)  # type: ignore[attr-defined] # should raise AttributeError
        except AttributeError as e:
            print(f"  ✓ Non-existent attribute access failed appropriately: {e}")

        # Test attribute modification (should fail)
        try:
            metacol.did = "should not do this"  # type: ignore[misc] # should raise AttributeError
        except AttributeError as e:
            print(f"  ✓ Attribute modification failed appropriately: {e}")

        # Test attribute deletion (should fail)
        try:
            del metacol.did  # pyright: ignore[reportAttributeAccessIssue]  # should raise AttributeError
        except AttributeError as e:
            print(f"  ✓ Attribute deletion failed appropriately: {e}")

        print(f"\nComplete metacol object: {metacol}")

    test_metacol()
