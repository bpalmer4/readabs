"""Create a TypeVar for either a Series or a DataFrame."""

from typing import TypeVar

from pandas import DataFrame, Series

Datatype = TypeVar("Datatype", Series, DataFrame)
