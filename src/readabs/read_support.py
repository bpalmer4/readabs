"""Support for reading ABS data functions.

This module provides validation and default value handling for keyword arguments
used across ABS data reading functions. It ensures consistent parameter handling
and validates that at least one data source option is enabled.
"""

from collections.abc import Mapping
from typing import Any, NotRequired, TypedDict

# Constants
HYPHEN = "---"


class SearchArgs(TypedDict):
    """Type definition for find_abs_id() / search_abs_meta() keyword arguments."""

    exact_match: NotRequired[bool]
    regex: NotRequired[bool]
    validate_unique: NotRequired[bool]
    verbose: NotRequired[bool]


class VerboseArgs(TypedDict):
    """Type definition for the keyword arguments left in search_abs_meta()'s **kwargs.

    exact_match, regex and validate_unique are explicit parameters there, so
    (per PEP 692) they cannot also appear in the unpacked TypedDict.
    """

    verbose: NotRequired[bool]


# Valid search kwargs are exactly the SearchArgs keys
_SEARCH_KWARGS: frozenset[str] = SearchArgs.__optional_keys__


class ReadArgs(TypedDict):
    """Type definition for ABS data reading arguments."""

    verbose: NotRequired[bool]
    ignore_errors: NotRequired[bool]
    get_zip: NotRequired[bool]
    get_excel_if_no_zip: NotRequired[bool]
    get_excel: NotRequired[bool]
    single_zip_only: NotRequired[str]
    single_excel_only: NotRequired[str]
    selected_excel: NotRequired[tuple[str, ...]]
    history: NotRequired[str]
    cache_only: NotRequired[bool]
    keep_non_ts: NotRequired[bool]
    zip_file: NotRequired[str]


# Default values for all supported arguments
# Note: 'url' is intentionally excluded - it's an explicit parameter of the
# public reader functions and should not be included in the args dict
DEFAULTS: ReadArgs = {
    "verbose": False,
    "ignore_errors": False,
    "get_zip": True,
    "get_excel_if_no_zip": True,
    "get_excel": False,
    "single_zip_only": "",
    "single_excel_only": "",
    "selected_excel": (),
    "history": "",
    "cache_only": False,
    "keep_non_ts": False,
    "zip_file": "",
}

# Arguments that enable data retrieval (at least one must be True/non-empty)
_DATA_SOURCE_ARGS = [
    "get_zip",
    "get_excel",
    "get_excel_if_no_zip",
    "single_zip_only",
    "single_excel_only",
    "selected_excel",
]

# Valid kwargs are exactly the ReadArgs keys; 'url' is an explicit parameter, not a kwarg
_VALID_KWARGS = set(DEFAULTS.keys())


def check_kwargs(kwargs: Mapping[str, object], name: str, valid: frozenset[str] | set[str] | None = None) -> None:
    """Warn if there are any invalid keyword arguments.

    Args:
        kwargs: keyword arguments to validate (a ReadArgs or SearchArgs TypedDict)
        name: Name of the calling function for error messages
        valid: the valid keyword names; defaults to the ReadArgs keys

    """
    if not isinstance(name, str):
        print("Function name must be a string")
        return

    valid_names = _VALID_KWARGS if valid is None else valid
    for arg_name in kwargs:
        if arg_name not in valid_names:
            print(f"{name}(): Unexpected keyword argument '{arg_name}'. Valid arguments are: {list(valid_names)}")


def get_args(kwargs: ReadArgs, name: str) -> dict[str, Any]:
    """Return a dictionary with validated arguments and defaults applied.

    Creates a dictionary containing only valid keyword arguments, with default
    values applied for missing keys. Validates that at least one data source
    option is enabled.

    Args:
        kwargs: ReadArgs keyword arguments from calling function
        name: Name of the calling function for error messages

    Returns:
        dict[str, Any]: Dictionary containing validated arguments with defaults

    Raises:
        ValueError: If no data source options are enabled
        TypeError: If inputs are not the correct type

    """
    # Input validation
    if not isinstance(name, str):
        raise TypeError("Function name must be a string")

    # Apply defaults for all known arguments
    args = {key: kwargs.get(key, default_value) for key, default_value in DEFAULTS.items()}

    # Check that at least one data source option is enabled
    has_zip = args["get_zip"]
    has_excel = args["get_excel"]
    has_excel_if_no_zip = args["get_excel_if_no_zip"]
    has_single_zip = bool(args["single_zip_only"])
    has_single_excel = bool(args["single_excel_only"])
    has_selected_excel = bool(args["selected_excel"])

    if not any([has_zip, has_excel, has_excel_if_no_zip, has_single_zip, has_single_excel, has_selected_excel]):
        raise ValueError(
            f"{name}(): At least one data source option must be enabled. Options are: {_DATA_SOURCE_ARGS}"
        )

    return args
