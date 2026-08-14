# open-rigbi
Open-data Risk Analysis of Global Mobile Broadband Infrastructure

This repository contains a codebase for assessing the global vulnerability of 
mobile infrastructure via OpenCelliD data. 

Paper citation
--------------

- Oughton, E.J., Russell, T., Oh, J., Ballan, S., Hall, J.W., 2023. Global 
vulnerability assessment of mobile telecommunications infrastructure to 
climate hazards using crowdsourced open data. https://doi.org/10.48550/arXiv.2311.04392

## Reproducible environment

[`environment.yml`](environment.yml) is the single dependency specification
for both the Python and R figure scripts. Its `nodefaults` entry restricts the
solve to `conda-forge`, so NumPy and the compiled geospatial libraries are
resolved as one compatible stack. From the repository root, create and
activate the tested environment with:

```console
conda env create --file environment.yml
conda activate rigbi-env
```

If an older `rigbi-env` already exists, do not update it in place. Remove and
recreate it so packages from the previous mixed-channel environment cannot be
retained:

```console
conda deactivate
conda env remove --name rigbi-env
conda env create --file environment.yml
conda activate rigbi-env
```

The data paths are configured relative to the repository by
`scripts/script_config.ini`. Run all commands below from the repository root.

## Regenerating publication figures

Figures 1, 3 and 5 (global coastal, riverine and tropical-cyclone impact
charts) are generated together:

```console
Rscript --vanilla vis/global_aggregate_estimates.R
```

Figures 2, 4 and 6 (the corresponding spatial cost maps) are generated with:

```console
python vis/vis_coast.py
python vis/vis_riverine.py
python vis/vis_trop_storm.py
```

The hazard-layer comparison figure is generated with:

```console
Rscript --vanilla vis/scenario_statistics_totals.r
```

The supplementary, non-dodged hazard-layer plots are generated with:

```console
Rscript --vanilla vis/scenario_statistics_totals_si.r
```

The cell-count descriptive figure first requires the consolidated cell-count
input. Generate the input and figure with:

```console
python scripts/cells.py
Rscript --vanilla vis/cell_counts.r
```

This last pair requires the per-country processed site layers under
`data/processed/<ISO3>/sites_new/`.

## Overview of scripts

The scripts involved can be broadly summarized as follows:

- `cells.py` create unique cell data per country.
- `coastal_lut.py` generates a lookup table of coastal regions. 
- `collect.py` contains functions to collect summary results. 
- `countries.py` processes country metadata. 
- `dl.py` downloads all necessary scenario hazard data layers.
- `misc.py` contains miscellaneous functions.
- `preprocess.py` preprocesses all boundaries, cell data and flood hazard layers for each country.
- `process.py` processes all flooding results. 
- `tropical_storms.py` processes all tropical storm results. 
- `validation.py` creates datasets to validate the results. 

Data citation
--------------

For the main input datasets, these can be accessed by the associated Zenodo repository. 

- Oughton, E. J. 2026. “OpenCelliD Data 2022_12_24.” Zenodo, March 7. https://doi.org/10.5281/zenodo.18904374.
