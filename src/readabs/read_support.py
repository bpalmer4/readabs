"""Support for reading ABS data functions.

This module provides validation and default value handling for keyword arguments
used across ABS data reading functions. It ensures consistent parameter handling
and validates that at least one data source option is enabled.
"""

from typing import Any, NotRequired, TypedDict

# Constants
HYPHEN = "---"


class ReadArgs(TypedDict):
    """Type definition for ABS data reading arguments."""

    verbose: NotRequired[bool]
    ignore_errors: NotRequired[bool]
    get_zip: NotRequired[bool]
    get_excel_if_no_zip: NotRequired[bool]
    get_excel: NotRequired[bool]
    single_zip_only: NotRequired[str]
    single_excel_only: NotRequired[str]
    history: NotRequired[str]
    cache_only: NotRequired[bool]
    keep_non_ts: NotRequired[bool]
    zip_file: NotRequired[str]
    url: NotRequired[str]


# Default values for all supported arguments
# Note: 'url' is intentionally excluded - it's handled as a separate parameter
# in grab_abs_url() and should not be included in the args dict
DEFAULTS: ReadArgs = {
    "verbose": False,
    "ignore_errors": False,
    "get_zip": True,
    "get_excel_if_no_zip": True,
    "get_excel": False,
    "single_zip_only": "",
    "single_excel_only": "",
    "history": "",
    "cache_only": False,
    "keep_non_ts": False,
    "zip_file": "",
}

# Arguments that enable data retrieval (at least one must be True/non-empty)
_DATA_SOURCE_ARGS = ["get_zip", "get_excel", "get_excel_if_no_zip", "single_zip_only", "single_excel_only"]

# Valid kwargs includes DEFAULTS plus 'url' (which is handled separately as a parameter)
_VALID_KWARGS = set(DEFAULTS.keys()) | {"url"}


def check_kwargs(kwargs: ReadArgs, name: str) -> None:
    """Warn if there are any invalid keyword arguments.

    Args:
        kwargs: ReadArgs keyword arguments to validate
        name: Name of the calling function for error messages

    """
    if not isinstance(name, str):
        print("Function name must be a string")
        return

    for arg_name in kwargs:
        if arg_name not in _VALID_KWARGS:
            print(
                f"{name}(): Unexpected keyword argument '{arg_name}'. Valid arguments are: {list(_VALID_KWARGS)}"
            )


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

    if not any([has_zip, has_excel, has_excel_if_no_zip, has_single_zip, has_single_excel]):
        raise ValueError(
            f"{name}(): At least one data source option must be enabled. Options are: {_DATA_SOURCE_ARGS}"
        )

    return args
