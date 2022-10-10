"""
Generate country/regional codes to pass to each node.

Written by Ed Oughton.

August 2022.

"""
import os
import sys
import configparser
import pandas as pd
import numpy as np
import geopandas as gpd
import random

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW = os.path.join(BASE_PATH, 'raw')
DATA_PROCESSED = os.path.join(BASE_PATH, 'processed')


def get_regional_id_information(countries):
    """
    Load in regional id information.

    """
    output = []

    # countries = pd.read_csv(path, encoding='latin-1')
    # country = countries[countries.iso3 == iso3]
    # country = country.to_dict('records')[0]

    # regional_level = int(country['gid_region'])

    for idx, country in countries.iterrows():

        gid_level = 'GID_{}'.format(country['gid_region'])

        folder = os.path.join(DATA_PROCESSED, country['iso3'], 'regions')

        filename = 'regions_{}_{}.shp'.format(
            int(country['gid_region']),
            country['iso3']
        )

        path = os.path.join(folder, filename)

        if os.path.exists(path):

            regions = gpd.read_file(path)
            regions = regions[gid_level]
            # regions = regions.to_dict('records')
            regions = regions.tolist()

            output = output + regions

    return output


if __name__ == "__main__":

    filename = "countries.csv"
    #filename = "failures.csv"
    path = os.path.join(DATA_RAW, filename)

    countries = pd.read_csv(path, encoding='latin-1')
    countries = countries[countries.Exclude == 0]

    #countries = countries[countries['Population'] > 5000000]
    #countries = countries.sort_values(by=['Population'], ascending=True)
    # countries = countries['iso3']

    regions = get_regional_id_information(countries)

    random.shuffle(regions)
    # print(regions)
    # countries.reindex(np.random.permutation(countries.index))

    #countries = countries[countries['iso3'] == 'USA']
    #print('USA')
    print(*regions, sep='\n')
