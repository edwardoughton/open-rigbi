"""
Gather cell count information.

Written by Ed Oughton.

February 2023
"""
import os
import json
import configparser
import pandas as pd
import geopandas as gpd

from misc import get_countries, get_regions

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW = os.path.join(BASE_PATH, 'raw')
DATA_PROCESSED = os.path.join(BASE_PATH, 'processed')

def count_cells(country):
    """
    Count unique cells by radio technology for each administrative region.

    This function iterates over all regions at the country’s configured
    administrative level, reads the corresponding unique site layers,
    and counts the number of cells by radio technology (2G, 3G, 4G, and 5G).
    The aggregated results are written to a country-level CSV file.

    Parameters
    ----------
    country : dict
        Dictionary containing country metadata, including the ISO3 code
        and regional configuration.
    """
    regional_level = country['gid_region']
    gid_level = 'gid_{}'.format(regional_level) #regional_level
    folder = os.path.join(DATA_PROCESSED, country['iso3'], 'sites', gid_level)

    regions_df = get_regions(country, regional_level)

    if len(regions_df) == 0:
        print("len(regions_df) == 0")
        return

    output = []

    for region in regions_df:
        
        region = region["GID_{}".format(regional_level)]
        
        filename = "{}_unique.gpkg".format(region)
        path_in = os.path.join(folder, filename)
        
        if not os.path.exists(path_in):
            print("path_in did not exist: {}".format(path_in))
            continue
        try:
            data = gpd.read_file(path_in)
        except:
            print('Failed to read in: {}'.format(path_in))
            continue
        
        data = data.to_dict('records')

        cells_2g = 0
        cells_3g = 0
        cells_4g = 0
        cells_5g = 0

        for row in data:
            
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

    filename = "cell_count_unique.csv"
    folder_out = os.path.join(DATA_PROCESSED, country['iso3'], 'sites')
    path_out = os.path.join(folder_out, filename)
    output.to_csv(path_out, index=False)

    return


def collect_cells(countries):
    """
    Aggregate regional cell counts across multiple countries.

    This function reads per-country regional cell count files, combines
    them into a single dataset, and writes the aggregated results to a
    consolidated CSV file. Countries without available cell count data
    are skipped.

    Parameters
    ----------
    countries : list of dict
        Iterable of country metadata dictionaries, each containing at
        least an ISO3 country code.
    """
    output = []

    for country in countries:

        filename = "cell_count_unique.csv"
        folder_in = os.path.join(DATA_PROCESSED, country['iso3'], 'sites')
        path_in = os.path.join(folder_in, filename)

        if not os.path.exists(path_in):
            continue
        
        print("Collecting cells for {}".format(country['iso3']))

        data = pd.read_csv(path_in)
        data = data.to_dict('records')
        output = output + data

    if not len(output) > 0:
        return

    output = pd.DataFrame(output)

    filename = "cell_count_regional_unique.csv"
    folder_out = os.path.join(DATA_PROCESSED, 'results', 'sites')
    if not os.path.exists(folder_out):
        os.makedirs(folder_out)
    path_out = os.path.join(folder_out, filename)
    output.to_csv(path_out, index=False)


if __name__ == "__main__":

    countries = get_countries()

    for country in countries:
        
        # if not country['iso3'] == 'RWA':
        #     continue
        
        print("Working on {}".format(country['iso3']))

        count_cells(country)

    collect_cells(countries)
