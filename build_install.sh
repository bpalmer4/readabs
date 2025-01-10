#!/bin/zsh
# make sure the version number is correct in:
# ./readabs/src/readabs/__init__.py

cd ~/readabs

~/readabs/build_docs.sh

if [ ! -d ./dist ]; then
    mkdir dist
fi
if [ -n "$(ls -A ./dist 2>/dev/null)" ]; then
  rm ./dist/*
fi

pip uninstall readabs

pip install -q build

python -m build

twine upload dist/*

pip install readabs

