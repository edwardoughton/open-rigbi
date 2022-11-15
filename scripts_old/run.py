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

from sites import (run_site_processing, extract_oci_site_info,
    collect_site_info, collect_regional_site_info)
from misc import get_countries, get_scenarios, get_regions
from flood_hazards import process_flooding_layers
from results import query_hazard_layers

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW = os.path.join(BASE_PATH, 'raw')
DATA_PROCESSED = os.path.join(BASE_PATH, 'processed')


if __name__ == "__main__":

    crs = 'epsg:4326'

    countries = get_countries()
    scenarios = get_scenarios()#[:10]

    failed = []

    for idx, country in countries.iterrows():

        # if not country['iso3'] in ['IRL']:
        #     continue
        # print(country)
        print('-- {}'.format(country['country']))

        # try:
        run_site_processing(country)

        process_flooding_layers(country, scenarios)
        # regions = get_regions(country, 1)
        # cProfile.run('query_hazard_layers(country, regions, technologies, scenarios)', 'profile.log')
        query_hazard_layers(country, get_regions(country, 1), scenarios)

        # except:
        #     print('Failed on {}'.format(country['country']))
        #     failed.append(country['country'])
        #     continue

    #     extract_oci_site_info(country)

    # collect_site_info(countries)

    # collect_regional_site_info(countries)

    print('--Complete')
