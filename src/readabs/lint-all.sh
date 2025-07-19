echo "------------------------"
echo "ruff check --fix and format ..."
ruff format *.py
ruff check --fix *.py
ruff format *.py

echo " "
echo "------------------------"
echo "mypy ..."
mypy *.py

echo " "
echo "------------------------"
echo "pyright ..."
pyright *.py

# report any lint overrides
echo " "
echo "------------------------"
echo "Check linting overrides ..."
grep "# type" *.py
grep -E "# mypy:.*disable" *.py
grep "# pylint" *.py
grep "cast(" *.py
grep "# noqa:" *.py

