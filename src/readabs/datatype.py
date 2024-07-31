"""Create a TypeVar for either a Series or a DataFrame"""

from typing import TypeVar
from pandas import Series, DataFrame

Datatype = TypeVar("Datatype", Series, DataFrame)
Datatype.__doc__ = "Either a pandas Series or DataFrame."
