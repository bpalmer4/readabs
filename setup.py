import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="readabs",
    version="0.0.1",
    author="Bryan Palmer",
    author_email="palmer.bryan@gmail.com",
    description="Read ABS time series data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/bpalmer4/readabs",
    packages=setuptools.find_packages(),
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
)

