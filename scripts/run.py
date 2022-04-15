"""


"""
import os
import configparser
import pandas as pd
import geopandas as gpd
import pyproj
from shapely.ops import transform
from shapely.geometry import shape, Point, mapping, LineString, MultiPolygon
from tqdm import tqdm

from sites import run_site_processing

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW = os.path.join(BASE_PATH, 'raw')
DATA_PROCESSED = os.path.join(BASE_PATH, 'processed')


if __name__ == "__main__":

    crs = 'epsg:4326'

    filename = "countries.csv"
    path = os.path.join(DATA_RAW, filename)
    countries = pd.read_csv(path, encoding='latin-1')
    countries = countries[countries.Exclude == 0]

    for idx, country in countries.iterrows():

        print('-- {}'.format(country['country']))

        try:
            run_site_processing(country['iso3'], country['lowest'])

        except:

            continue

    print('--Complete')
