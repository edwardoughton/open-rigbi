"""
Generate an ISO3 code to pass to each node.

Written by Ed Oughton.

August 2022.

"""
import os
import sys
import configparser
import pandas as pd

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW = os.path.join(BASE_PATH, 'raw')
DATA_PROCESSED = os.path.join(BASE_PATH, 'processed')


if __name__ == "__main__":

    filename = "countries.csv"
    path = os.path.join(DATA_RAW, filename)

    countries = pd.read_csv(path, encoding='latin-1')
    countries = countries[countries.Exclude == 0]

    countries = countries[countries['Population'] > 5000000]
    countries = countries.sort_values(by=['Population'], ascending=True)
    countries = countries['iso3']

    print(*countries, sep='\n')
