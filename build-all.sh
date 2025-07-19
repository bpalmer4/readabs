#!/bin/zsh
# make sure the version number is correct:
# ~/readabs/pyproject.toml

# --- cd readabs home and get ready
cd ~/readabs
uv pip uninstall readabs
deactivate

# --- clean out the dist folder
if [ ! -d ./dist ]; then
    mkdir dist
fi
if [ -n "$(ls -A ./dist 2>/dev/null)" ]; then
  rm ./dist/*
fi

# --- sync and build
uv lock --upgrade  # --upgrade to get the latest dependencies
uv sync --no-dev  # --no-dev to avoid installing dev dependencies
uv build

# --- install new readabs locally
uv sync  # install with the development dependencies

# --- build documentation
source .venv/bin/activate  # we need an environment to get pdoc 
~/readabs/build-docs.sh

# --- if everything is good publish and git
echo "\nAnd if everything is okay ..."
echo "uv publish --token MY_TOKEN_HERE"
echo "And don't forget to upload to github"
