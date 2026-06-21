# Reproducibility package — "Where to base air rescue" (Socio-Economic Planning Sciences)

Author: Maciej Marcin Kasperek (ORCID 0009-0008-7419-0851).
This package reproduces every quantitative result, both figures and the coverage and
optimality figures reported in the manuscript, from public, operator-independent inputs.

## Contents
- `loc28.json` — the model-optimised coordinates of all network locations
  (rows: type, name, sector, airfield, ICAO, lat_airfield, lon_airfield, status,
  lat_model, lon_model; decimal comma). Primary bases are the 7 CRL + 14 CT.
- `mip_curve.py` — builds a common candidate grid (18 km lattice + the 7 fixed CRL),
  evaluates surface coverage on a 5 km demand grid, runs the greedy set-cover heuristic
  and the exact maximal covering location problem (MCLP) for p = 9..21 via PuLP/CBC,
  and writes the greedy-vs-optimum curve. Reproduces Section 3.5 and the data for Figure 2.
- `mip_validate.py` — single-point exact-vs-greedy check at the operating point.
- `generate_fig2_optgap.py` — renders Figure 2 (greedy vs MCLP optimum) as vector PDF + PNG.
- `generate_map_SEPS_EN.py` — renders Figure 1 (the network map, 30-minute coverage) as
  vector PDF + PNG. White background, no title/stats panel (these are in the caption).
- `fetch_gadm.py` — downloads the GADM v4.1 boundary into `geo/`. The file is not shipped, the GADM licence forbids redistribution. Run this once before the figures.
- `geo/gadm41_POL_2.json` — administrative boundary, GADM v4.1 (land area of Poland). Not shipped, produced by `fetch_gadm.py`.
- `geo/pl_pop_1km.tif` — WorldPop 2020 population raster, 1 km, clipped to Poland. CC-BY 4.0, shipped here.

## Method parameters (as in the manuscript)
- Operating radius R = ((30 − 5) / 60) × 250 km ≈ 104.2 km
  (30-minute window, 5-minute crew activation, 250 km/h cruise).
- Projection: PL-1992 (EPSG:2180). Evaluation grid: 1 km cells (312,127 over land).
- Coverage threshold for H1: 95 per cent of surface.

## Data provenance (external, public)
- GADM v4.1 — https://gadm.org/. The GADM licence allows academic use and the making of maps for research articles, but does not allow redistribution of the data. The boundary file is therefore not shipped here. Run `python3 fetch_gadm.py` to download it into `geo/`.
- WorldPop 2020, Poland, 1 km — https://www.worldpop.org/. Released under CC-BY 4.0, the clipped raster is shipped here in `geo/`.
Cite both original sources in any derived work.

## How to run
```
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python3 fetch_gadm.py          # -> geo/gadm41_POL_2.json (GADM boundary, not shipped)
python3 mip_curve.py            # -> curve.json (greedy vs MCLP optimum)
python3 generate_fig2_optgap.py # -> Figure_2 (PDF + PNG)
python3 generate_map_SEPS_EN.py # -> Figure_1 (PDF + PNG)
```
Paths inside the scripts assume this folder; adjust the `/home/claude/...` paths to your
local copy if needed (boundary and raster are under `geo/`).

## Expected results
- Network of 21 primary bases: 99.95 per cent surface coverage, 99.99 per cent population
  coverage within 30 minutes.
- Greedy within 0.2 percentage points of the proven MCLP optimum at the operating point.
- Sensitivity: 99.03 per cent surface coverage under the realistic scenario.

## Licence
Code: Apache 2.0. Data: as per GADM and WorldPop terms. Coordinates (`loc28.json`): CC BY 4.0.
The published version of record will be archived with a citable DOI (Zenodo).
