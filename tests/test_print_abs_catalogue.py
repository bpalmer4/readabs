"""Test the print_abs_catalogue() in readabs.py package."""

print("\n\n")
print("=" * 80)
print("Testing print_abs_catalogue()")
print("=" * 80)

import sys

sys.path.append("../src/readabs")

import readabs as ra

ra.print_abs_catalogue()
