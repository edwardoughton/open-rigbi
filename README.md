# open-rigbi
Open-data Risk Analysis of Global Mobile Broadband Infrastructure

This repository contains a codebase for assessing the global vulnerability of 
mobile infrastructure via OpenCelliD data. 

Paper citation
--------------

- Oughton, E.J., Russell, T., Oh, J., Ballan, S., Hall, J.W., 2023. Global 
vulnerability assessment of mobile telecommunications infrastructure to 
climate hazards using crowdsourced open data. https://doi.org/10.48550/arXiv.2311.04392


## Using the code

The recommended approach to using `open-rigbi` is via conda.

First, create a conda environment as follows:

    conda create --name rigbi-env python=3.7

Then activate it:

    conda activate rigbi-env

Finally, install the necessary packages, such as `geopandas`:

    conda install --file requirements.txt


## Overview of scripts

The scripts involved can be broadly summarized as follows:

- `dl.py` downloads all necessary scenario hazard data layers.
- `flood_hazards.py` preprocesses the flood hazard layers for each country.
- `sites.py` preprocesses all cell site data.
- `pop.py` preprocesses all population datalayers.
- `distances.py` calculates the distance lookup from cells to grid tiles.
- `econ.py` calculates the economic impacts of infrastructure damage.
