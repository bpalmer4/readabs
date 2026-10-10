uv lock --upgrade
uv sync --upgrade
# to pick up a new 3.14.x patch: uv python upgrade 3.14
# to move to a new Python version: change .python-version, then rm -rf .venv && uv sync

