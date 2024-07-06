"""abs_meta_data_sypport.py

Support for working with ABS meta data."""

from collections import namedtuple

Metacol = namedtuple("Metacol", 
	["did", "stype", "id", "start", "end", "num", "unit", "dtype",
	"freq", "cmonth", "table", "tdesc", "cat",]
)

metacol = Metacol(
	did = "Data Item Description",
	stype = "Series Type",
	id = "Series ID",
	start = "Series Start",
	end = "Series End",
	num = "No. Obs.",
	unit = "Unit",
	dtype = "Data Type",
	freq = "Freq.",
	cmonth = "Collection Month",
	table = "Table",
	tdesc = "Table Description",
	cat = "Catalogue number",
)


# --- testing
if __name__ == "__main__":
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
        metacol.did = "value"  # should raise an AttributeError
    except AttributeError as e:
        print(f"failed appropriately: {e}")

    try:
        del metacol.did  # should raise an AttributeError
    except AttributeError as e:
        print(f"failed appropriately: {e}")

    print(metacol)
