"""
Generate country regional codes to pass to each node.

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

    for idx, country in countries.iterrows():

        #if not country['iso3'] in ['BEL','BIH','BRB','EST','GUM','KHM','LSO','TWN','VGB', 'AND',
        #    'BFA','UBZ','BMU','BTN','CYM','DJI','FRO','ISR','KNA','LCA','MLI','MNG','MUS','PRY','TCA','WSM']: #'GHA'
        #    continue

        #if not country['iso3'] in ['USA']:#,'IND','ARG','AFG']:
        #    continue

        gid_level = 'GID_{}'.format(int(country['gid_region']))

        folder = os.path.join(DATA_PROCESSED, country['iso3'], 'regions')

        filename = 'regions_{}_{}.shp'.format(
            int(country['gid_region']),
            country['iso3']
        )

        path = os.path.join(folder, filename)
        
        if os.path.exists(path):
            
            regions = gpd.read_file(path)#[:1] 
            regions = regions[gid_level]
            regions = regions.tolist()
            output = output + regions
    print(len(output))
    return output


if __name__ == "__main__":

    filename = "countries.csv"

    path = os.path.join(DATA_RAW, filename)

    countries = pd.read_csv(path, encoding='latin-1')
    countries = countries[countries.Exclude == 0]
    # #countries = countries[countries['iso3'] == 'USA']
    # countries = countries[countries['iso3'].isin(['ARG','USA'])]
    # countries = countries['iso3']
    # countries.tolist()
    # print(*countries, sep='\n')    

    regions = get_regional_id_information(countries)#[:1]
    # print(len(regions))
    # random.shuffle(regions)
    print(*regions, sep='\n')
