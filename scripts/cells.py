"""
Gather cell count information.

Written by Ed Oughton.

February 2023

"""
import os
import json
import configparser
import pandas as pd

from misc import get_countries, get_regions

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW = os.path.join(BASE_PATH, 'raw')
DATA_PROCESSED = os.path.join(BASE_PATH, 'processed')

def count_cells(country):
    """
    Add up cells by technology.

    """
    regional_level = country['gid_region']
    gid_level = 'GID_{}'.format(regional_level) #regional_level
    folder = os.path.join(DATA_PROCESSED, country['iso3'], 'sites', gid_level)

    regions_df = get_regions(country, regional_level)

    if len(regions_df) == 0:
        return

    output = []

    for idx, region in regions_df.iterrows():

        region = region[gid_level]

        filename = "{}.csv".format(region)
        path_in = os.path.join(folder, filename)

        if not os.path.exists(path_in):
            continue

        data = pd.read_csv(path_in)

        cells_2g = 0
        cells_3g = 0
        cells_4g = 0
        cells_5g = 0

        for idx, row in data.iterrows():

            if row['radio'] == 'GSM':
                cells_2g += 1
            elif row['radio'] == 'UMTS':
                cells_3g += 1
            elif row['radio'] == 'LTE':
                cells_4g += 1
            elif row['radio'] == 'NR':
                cells_5g += 1

        output.append({
            "iso3": country['iso3'],
            "gid_level": gid_level,
            "gid_id": region,
            "cells_2g": cells_2g,
            "cells_3g": cells_3g,
            "cells_4g": cells_4g,
            "cells_5g": cells_5g,
        })

    if not len(output) > 0:
        return

    output = pd.DataFrame(output)

    filename = "cell_count.csv"
    folder_out = os.path.join(DATA_PROCESSED, country['iso3'], 'sites')
    path_out = os.path.join(folder_out, filename)
    output.to_csv(path_out, index=False)

    return


def collect_cells(countries):
    """
    Collect all cells.

    """
    output = []

    for idx, country in countries.iterrows():

        filename = "cell_count.csv"
        folder_in = os.path.join(DATA_PROCESSED, country['iso3'], 'sites')
        path_in = os.path.join(folder_in, filename)

        if not os.path.exists(path_in):
            continue

        data = pd.read_csv(path_in)
        data = data.to_dict('records')
        output = output + data

    if not len(output) > 0:
        return

    output = pd.DataFrame(output)

    filename = "cell_count_regional.csv"
    folder_out = os.path.join(DATA_PROCESSED, 'results', 'sites')
    if not os.path.exists(folder_out):
        os.makedirs(folder_out)
    path_out = os.path.join(folder_out, filename)
    output.to_csv(path_out, index=False)


if __name__ == "__main__":

    countries = get_countries()

    for idx, country in countries.iterrows():

        # if not country['iso3'] == 'RWA':
        #     continue

        count_cells(country)

    collect_cells(countries)
