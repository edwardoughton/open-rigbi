"""
Find vulnerable population (poorest 40%) without connectivity.

Written by Ed Oughton.

July 2022.

"""
import os
import configparser
import json
import csv
import geopandas as gpd
import pandas as pd
import glob
import pyproj
from shapely.geometry import MultiPolygon, mapping, MultiLineString
from shapely.ops import transform, unary_union, nearest_points
import rasterio
from rasterio.mask import mask
from rasterstats import zonal_stats
from tqdm import tqdm
from shapely.geometry import box, shape
from rasterio.merge import merge
import numpy as np

from misc import get_countries, technologies

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW = os.path.join(BASE_PATH, 'raw')
DATA_PROCESSED = os.path.join(BASE_PATH, 'processed')



def find_uncovered_poor(country):
    """
    Intersect uncovered areas with the locations of the
    bottom 40% of the income distribution.

    """
    filename = "bottom_40_perc.shp"
    folder = os.path.join(DATA_PROCESSED, country['iso3'], 'relative_wealth_index')
    path_in = os.path.join(folder, filename)
    vulnerable_pop = gpd.read_file(path_in, crs='epsg:4326')#[:2]

    for tech in technologies:

        filename = 'baseline_uncovered_{}.shp'.format(tech)
        folder = os.path.join(DATA_PROCESSED, country['iso3'], 'coverage')
        path = os.path.join(folder, filename)

        if not os.path.exists(path):
            continue

        uncovered = gpd.read_file(path, crs='epsg:4326')
        uncovered = uncovered.to_crs(4326)
        uncovered = uncovered.loc[uncovered['covered'] == 'Uncovered']

        uncovered_poor = vulnerable_pop.overlay(uncovered, how='intersection')

        uncovered_poor = uncovered_poor.to_crs(3857)

        uncovered_poor['area_km2'] = uncovered_poor['geometry'].area / 1e6

        uncovered_poor = uncovered_poor.loc[uncovered_poor['area_km2'] >= 5.5]

        uncovered_poor = uncovered_poor.to_crs(4326)

        folder_out = os.path.join(DATA_PROCESSED, country['iso3'], 'uncovered_poor')
        if not os.path.exists(folder_out):
            os.mkdir(folder_out)
        filename = 'baseline_uncovered_poor_{}.shp'.format(tech)
        path_out = os.path.join(folder_out, filename)
        uncovered_poor.to_file(path_out, crs='epsg:4326')

    return


if __name__ == '__main__':

    countries = get_countries()

    for idx, country in tqdm(countries.iterrows(), total=countries.shape[0]):

        if not country['iso3'] in ['GHA']: #, 'GHA']:
            continue

        find_uncovered_poor(country)
