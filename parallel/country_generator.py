"""
Generate country iso3 codes to pass to each node.

Written by Ed Oughton.

February 2023.

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


def get_country_iso3_codes(countries):
    """
    Load in country information.

    """
    output = []

    for idx, country in countries.iterrows():

        output.append(country['iso3'])

    return output


if __name__ == "__main__":

    filename = "countries.csv"

    path = os.path.join(DATA_RAW, filename)

    countries = pd.read_csv(path, encoding='latin-1')
    countries = countries[countries.Exclude == 0]

    #countries = countries[countries['iso3'] == 'USA']

    country_iso3_codes = get_country_iso3_codes(countries)#[:1]

    # random.shuffle(country_iso3_codes)

    print(*country_iso3_codes, sep='\n')
