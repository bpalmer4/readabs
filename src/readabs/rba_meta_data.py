"""Support for working with RBA meta data."""

from dataclasses import dataclass


@dataclass(frozen=True)
class _RbaMetacol:
    """A dataclass to hold the names of the columns in the RBA meta data."""

    # pylint: disable=too-many-instance-attributes
    title: str = "Title"
    desc: str = "Description"
    freq: str = "Frequency"
    type: str = "Type"
    unit: str = "Units"
    src: str = "Source"
    pub: str = "Publication date"
    id: str = "Series ID"
    table: str = "Table"
    tdesc: str = "Table Description"


rba_metacol = _RbaMetacol()
