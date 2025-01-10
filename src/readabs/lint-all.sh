echo "black"
black *.py

echo "pylint"
pylint *.py

echo "mypy"
mypy *.py

echo "ruff"
ruff check *.py

# report any lint overrides
echo " "
echo "Check linting overrides ..."
grep "# type" *.py
grep "# pylint" *.py

