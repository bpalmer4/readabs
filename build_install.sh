#!/bin/zsh
# make sure the version number is correct in:
# ./readabs/src/readabs/__init__.py

rm dist/*

pip uninstall readabs

pip install -Ue .

pip install -q build

python -m build

twine upload dist/*

