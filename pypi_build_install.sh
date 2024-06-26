#!/bin/zsh
# make sure the version number is correct in setup.py

pip uninstall readabs

pip install -Ue .

pip install -q build

python -m build

twine upload dist/*

