"""Generate the catalogue_map.py file."""

# --- imports
from io import StringIO
import pandas as pd
from get_url_cache import get_file


# --- functions
# private
def _get_abs_directory() -> pd.DataFrame:
    """Return a DataFrame of ABS Catalogue numbers."""

    # get ABS web page of catalogue numbers
    url = "https://www.abs.gov.au/about/data-services/help/abs-time-series-directory"
    page = get_file(url)
    links = pd.read_html(StringIO(page.decode("utf-8")), extract_links="body")[1]  # second table on the page

    # extract catalogue numbers
    cats = links["Catalogue Number"].apply(pd.Series)[0]
    urls = links["Topic"].apply(pd.Series)[1]
    root = "https://www.abs.gov.au/statistics/"
    snip = urls.str.replace(root, "")
    snip = (
        snip[~snip.str.contains("http")].str.replace("-", " ").str.title()
    )  # remove bad cases
    frame = snip.str.split("/", expand=True).iloc[:, :3]
    frame.columns = pd.Index(["Theme", "Parent Topic", "Topic"])
    frame["URL"] = urls
    cats = cats[frame.index]
    cat_index = cats.str.replace("(Ceased)", "").str.strip()
    status = pd.Series(" ", index=cats.index).where(cat_index == cats, "Ceased")
    frame["Status"] = status
    frame.index = pd.Index(cat_index)
    frame.index.name = "Catalogue ID"
    return frame


def produce_catalogue_map():
    """Generate the catalogue_map.py file."""
    directory = _get_abs_directory()
    with open("abs_catalogue_map.py", "w", encoding="utf-8") as file:
        file.write('"""Catalogue map for ABS data."""\n\n')
        file.write("import pandas as pd\n")
        file.write("from io import StringIO\n\n")
        file.write("def catalogue_map() -> pd.DataFrame:\n")
        file.write('    """Return the catalogue map."""\n\n')
        file.write(f'    csv = """{directory.to_csv()}"""\n')
        file.write("    return pd.read_csv(StringIO(csv), index_col=0)\n\n")


if __name__ == "__main__":
    produce_catalogue_map()
