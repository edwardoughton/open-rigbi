"""
Segment data 

Ed Oughton

February 2022

"""
# import sys
import os
import configparser
import pandas as pd

# from misc import get_countries, process_country_shapes, process_regions, get_regions, get_scenarios

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__),'..', 'scripts', 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW = os.path.join(BASE_PATH, 'raw')
DATA_PROCESSED = os.path.join(BASE_PATH, 'processed')


def process_countries_metadata():
    """
    Segment countries data.

    """
    filename = "countries.csv"
    path = os.path.join(DATA_RAW, filename)

    countries = pd.read_csv(path, encoding='latin-1')
    countries = countries[countries['Exclude'] == 0]

    iso3_unique = countries['iso3'].unique()

    for iso3 in iso3_unique:

        country = countries[countries.iso3 == iso3]

        folder_out = os.path.join(DATA_PROCESSED, iso3)

        if not os.path.exists(folder_out):
            continue

        path_out = os.path.join(folder_out, '{}.csv'.format(iso3))

        country.to_csv(path_out, index=False)
        
    return


if __name__ == "__main__":

    process_countries_metadata()