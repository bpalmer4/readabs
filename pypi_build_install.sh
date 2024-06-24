# make sure the version number is correct in setup.py

python setup.py sdist

twine upload dist/*
