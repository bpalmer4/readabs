"""Support for the read ABS data functions, all of which take the
same keyword arguments. This module provides a way to check for
unexpected keyword arguments and to provide default values for
those arguments that are not provided."""

from typing import Any

HYPHEN = "---"

DEFAULTS: dict[str, Any] = {
    # argument_name: default_value,
    "verbose": False,
    "ignore_errors": False,
    "get_zip": True,
    "get_excel_if_no_zip": True,
    "get_excel": False,
    "single_zip_only": "",
    "single_excel_only": "",
    "history": "",
    "cache_only": False,
}


def check_kwargs(kwargs: dict[str, Any], name: str) -> None:
    """Warn if there are any invalid keyword args."""
    for k in kwargs:
        if k not in DEFAULTS:
            print(f"{name}(): Unexpected keyword argument {k}")


def get_args(kwargs: dict[str, Any], name: str) -> dict[str, Any]:
    """Return a dictionary with only the valid kwargs
    (and their default values if a valid key is missing from kwargs).
    Specifically check that one of the following flags is True:
    [get_zip, get_excel, get_excel_if_no_zip, get_zip, single_zip_only,
    single_excel_only]."""

    args = {k: kwargs.get(k, v) for k, v in DEFAULTS.items()}
    if (
        not args["get_zip"]
        and not args["get_excel"]
        and not args["get_excel_if_no_zip"]
        and not args["single_zip_only"]
        and not args["single_excel_only"]
    ):
        raise ValueError(
            f"{name}(): At least one of get_zip or get_excel or get_excel_if_no_zip "
            + "or single_zip_only or single_excel_only must be True."
        )

    return args
