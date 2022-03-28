# open-rigbi
Open-data Risk Analysis of Global Broadband Infrastructure

This repository contains a codebase for assessing the global vulnerability of broadband
infrastructure.


## Using the code

The recommended approach to using `rigbi` is via conda.

First, create a conda environment as follows:

    conda create --name rigbi python=3.7

Install andy required packages, such as `geopandas`:

    conda install geopandas rasterio rasterstats


## Overview of scripts

The scripts involved can be broadly summarized as follows:

- `dl.py` downloads all necessary scenario hazard data layers.
- `flood_hazards.py` preprocesses the flood hazard layers for each country.
- `sites.py` preprocesses all cell site data.
- `pop.py` preprocesses all population datalayers.
- `distances.py` calculates the distance lookup from cells to grid tiles.


- `econ.py` calculates the economic impacts of infrastructure damage.
