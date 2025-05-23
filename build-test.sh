#!/bin/zsh
# make sure the version number is correct in:
# (1) ~/readabs/src/readabs/__init__.py
# (2) ~/readabs/pyproject.toml

cd ~/readabs

~/readabs/build-docs.sh

if [ ! -d ./dist ]; then
    mkdir dist
fi
if [ -n "$(ls -A ./dist 2>/dev/null)" ]; then
  rm ./dist/*
fi

uv sync

uv build

uv pip install dist/readabs*gz

echo "And if everything is okay ..."
echo "uv publish --token MY_TOKEN_HERE"

