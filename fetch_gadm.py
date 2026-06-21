#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Fetch the GADM v4.1 Poland level-2 administrative boundary.

GADM data are free for academic and non-commercial use but may not be
redistributed without permission (https://gadm.org/license.html). The
boundary file is therefore not shipped in this repository. Run this
script once before the analysis to place it in geo/. The figures in the
article were produced from this exact file, md5 recorded below.

Attribution. Global Administrative Areas (GADM), version 4.1,
https://gadm.org, used under the GADM license for academic research.
The population raster shipped in geo/ is WorldPop 2020 under CC-BY 4.0.
"""
import hashlib
import io
import sys
import urllib.request
import zipfile
from pathlib import Path

URL = "https://geodata.ucdavis.edu/gadm/gadm4.1/json/gadm41_POL_2.json.zip"
DEST = Path(__file__).resolve().parent / "geo" / "gadm41_POL_2.json"
EXPECTED_MD5 = "fa8394c05b5ea5e182644bec10e3d678"
MEMBER = "gadm41_POL_2.json"


def main():
    if DEST.exists():
        print(f"Boundary already present, nothing to do.\n  {DEST}")
        return 0
    DEST.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading GADM v4.1 Poland level 2.\n  {URL}")
    try:
        req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=180) as r:
            blob = r.read()
    except Exception as exc:
        print(f"\nDownload failed. {exc}", file=sys.stderr)
        print(
            "Manual fallback. Open https://gadm.org/download_country.html, "
            "pick Poland, format GeoJSON, level 2, then place "
            f"{MEMBER} into the geo/ folder next to this script.",
            file=sys.stderr,
        )
        return 1
    try:
        with zipfile.ZipFile(io.BytesIO(blob)) as archive:
            name = next(n for n in archive.namelist() if n.endswith(MEMBER))
            DEST.write_bytes(archive.read(name))
    except (zipfile.BadZipFile, StopIteration) as exc:
        print(f"\nUnexpected archive content. {exc}", file=sys.stderr)
        return 1
    md5 = hashlib.md5(DEST.read_bytes()).hexdigest()
    print(f"Saved {DEST}\n  md5 {md5}")
    if md5 == EXPECTED_MD5:
        print("  md5 matches the file used in the article.")
    else:
        print(
            f"  Note, md5 differs from the article file ({EXPECTED_MD5}). "
            "This can happen if GADM re-released the boundary or re-serialised "
            "the file, results may shift slightly.",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
