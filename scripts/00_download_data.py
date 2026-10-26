"""
Download the Online Retail II dataset from the UCI Machine Learning Repository
into data/raw/.

The file is about 45 MB, which is why it is not committed to the repository.
Running this script once makes the rest of the pipeline reproducible.

Dataset : Online Retail II (UCI dataset 502)
Licence : CC BY 4.0
Page    : https://archive.ics.uci.edu/dataset/502/online+retail+ii

Usage: python scripts/00_download_data.py
"""

import io
import urllib.request
import zipfile
from pathlib import Path

URL = "https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip"
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
TARGET = RAW / "online_retail_II.xlsx"


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    if TARGET.exists():
        print("Already downloaded:", TARGET)
        return

    print("Downloading", URL)
    print("(about 45 MB, this can take a minute)")
    request = urllib.request.Request(URL, headers={"User-Agent": "portfolio-project"})
    with urllib.request.urlopen(request, timeout=300) as response:
        payload = response.read()

    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        names = [n for n in archive.namelist() if n.lower().endswith(".xlsx")]
        if not names:
            raise SystemExit("No .xlsx file found inside the archive: " + str(archive.namelist()))
        with archive.open(names[0]) as source:
            TARGET.write_bytes(source.read())

    print("Wrote", TARGET, "({:.1f} MB)".format(TARGET.stat().st_size / 1_048_576))
    print("Next step: python scripts/01_clean_data.py")


if __name__ == "__main__":
    main()
