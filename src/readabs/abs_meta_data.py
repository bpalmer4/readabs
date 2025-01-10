"""Support for working with ABS meta data."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Metacol:
    """A dataclass to hold the names of the columns in the ABS meta data."""

    # pylint: disable=too-many-instance-attributes
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


metacol = Metacol()
"""An instance of the Metacol dataclass. metacol is a 
frozen dataclass, so its attributes cannot be changed. 
It is used to hold the names of the columns for the 
DataFrame of the ABS meta data."""


# --- testing
if __name__ == "__main__":

    def test_metacol():
        """Quick test of the Metacol dataclass."""

        print(metacol.did)
        print(metacol.stype)
        print(metacol.id)
        print(metacol.start)
        print(metacol.end)
        print(metacol.num)
        print(metacol.unit)
        print(metacol.dtype)
        print(metacol.freq)
        print(metacol.cmonth)
        print(metacol.table)
        print(metacol.tdesc)
        print(metacol.cat)

        try:
            print(metacol.does_not_exist)  # should raise an AttributeError
        except AttributeError as e:
            print(f"failed approrpriately: {e}")

        try:
            metacol.did = "should not do this"  # should raise an AttributeError
        except AttributeError as e:
            print(f"failed appropriately: {e}")

        try:
            del metacol.did  # should raise an AttributeError
        except AttributeError as e:
            print(f"failed appropriately: {e}")

        print(metacol)

    test_metacol()
