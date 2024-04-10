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

    conda create --name rigbi-env

Then activate it:

    conda activate rigbi-env

Finally, install the necessary packages, such as `geopandas`:

    conda env update --file environment_linux.yaml # If on Linux
    conda env update --file environment_windows.yaml # If on Windows

If you add a `python=` argument to either of the two commands above, you can constrain the version of Python that Anaconda uses. By default, this project requires Python 3.9 and that is the version installed by running the env update command.

## Overview of scripts

The scripts involved can be broadly summarized as follows:

- `dl.py` downloads all necessary scenario hazard data layers.
- `preprocess.py` preprocesses all boundaries, cell data and flood hazard layers for each country.
- `coastal_lut.py` generates a lookup table of coastal regions. 
- `process.py` processes all results. 

