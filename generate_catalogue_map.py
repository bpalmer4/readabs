"""Generate the abs_catalogue_map.py file."""

# --- imports
from pathlib import Path
from datetime import datetime

import pandas as pd
from pandas import DataFrame, Series, Index


# --- functions
def main():
    """Generate the catalogue_map.py file."""

    # --- initialisation
    catalogue_file_name = "./src/readabs/abs_catalogue_map.py"
    back_up_dir = "./old-abs-catalogue-maps"
    Path(back_up_dir).mkdir(exist_ok=True)

    # --- save the old catalogue map
    old_catalogue_map = Path(catalogue_file_name)
    if old_catalogue_map.exists() and old_catalogue_map.is_file():
        modified_time = old_catalogue_map.stat().st_mtime
        ymd = datetime.fromtimestamp(modified_time).strftime("%Y-%b-%d")
        (
            Path(catalogue_file_name)
            .rename(Path(back_up_dir, f"{ymd}-{catalogue_file_name.split("/")[-1]}"))
        )

    # --- generate the new catalogue map
    directory = get_abs_directory()
    with open(catalogue_file_name, "w", encoding="utf-8") as file:
        file.write('"""Catalogue map for ABS data."""\n\n')
        file.write("from io import StringIO\n\n")
        file.write("from pandas import DataFrame, read_csv\n")
        file.write("def abs_catalogue() -> DataFrame:\n")
        file.write('    """Return the catalogue map."""\n\n')
        file.write(f'    csv = """{directory.to_csv()}"""\n')
        file.write("    return read_csv(StringIO(csv), index_col=0)\n")


def get_abs_directory() -> DataFrame:
    """Return a DataFrame of ABS Catalogue numbers."""

    # get ABS web page of catalogue numbers
    url = "https://www.abs.gov.au/about/data-services/help/abs-time-series-directory"
    links = pd.read_html(url, extract_links="body")[
        1
    ]  # second table on the page

    # extract catalogue numbers
    cats = links["Catalogue Number"].apply(Series)[0]
    urls = links["Topic"].apply(Series)[1]
    root = "https://www.abs.gov.au/statistics/"
    snip = urls.str.replace(root, "")
    snip = (
        snip[~snip.str.contains("http")].str.replace("-", " ").str.title()
    )  # remove bad cases
    frame = snip.str.split("/", expand=True).iloc[:, :3]
    frame.columns = Index(["Theme", "Parent Topic", "Topic"])
    frame["URL"] = urls
    cats = cats[frame.index]
    cat_index = cats.str.replace("(Ceased)", "").str.strip()
    status = Series(" ", index=cats.index).where(cat_index == cats, "Ceased")
    frame["Status"] = status
    frame.index = Index(cat_index)
    frame.index.name = "Catalogue ID"
    return frame


if __name__ == "__main__":
    main()
