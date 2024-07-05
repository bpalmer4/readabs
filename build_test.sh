#!/bin/zsh
# make sure the version number is correct in:
# ./readabs/src/readabs/__init__.py

cd ~/readabs

rm dist/*

pip uninstall readabs

pip install -q build

python -m build

cd dist

pip install readabs*.tar.gz

