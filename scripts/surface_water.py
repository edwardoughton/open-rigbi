"""
Process surface water by country.

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

from misc import get_countries

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW = os.path.join(BASE_PATH, 'raw')
DATA_PROCESSED = os.path.join(BASE_PATH, 'processed')


def process_surface_water(country):
    """
    Load in intersecting raster layers, and export large
    water bodies as .shp.

    Parameters
    ----------
    country : string
        Country parameters.

    """
    output = []

    filename = 'surface_water.shp'
    folder = os.path.join(DATA_PROCESSED, country['iso3'], 'surface_water')
    path_out = os.path.join(folder, filename)
    if not os.path.exists(folder):
        os.makedirs(folder)

    path_national = os.path.join(DATA_PROCESSED, country['iso3'], 'national_outline.shp')

    if os.path.exists(path_national):
        polygon = gpd.read_file(path_national, crs='4326')
    else:
        print('Must Generate National Shapefile first')

    poly_bounds = polygon['geometry'].total_bounds
    poly_bbox = box(*poly_bounds, ccw = False)

    path_lc = os.path.join(DATA_RAW, 'global_surface_water')

    surface_files = [
        os.path.abspath(os.path.join(path_lc, f)
        ) for f in os.listdir(path_lc) if f.endswith('.tif')
    ]

    for surface_file in surface_files:

        path = os.path.join(path_lc, surface_file)

        src = rasterio.open(path, 'r+')

        tiff_bounds = src.bounds
        tiff_bbox = box(*tiff_bounds)

        if tiff_bbox.intersects(poly_bbox):

            print('-Working on {}'.format(surface_file))

            data = src.read()
            data[data < 10] = 0
            data[data >= 10] = 1
            polygons = rasterio.features.shapes(data, transform=src.transform)
            for poly, value in polygons:
                if value > 0:
                    output.append({
                        'geometry': poly,
                        'properties': {
                            'value': value
                        }
                    })


    output = gpd.GeoDataFrame.from_features(output, crs='epsg:4326')

    mask = output.area > country['threshold']
    output = output.loc[mask]

    filename = 'national_outline.shp'
    path = os.path.join(DATA_PROCESSED, country['iso3'], filename)
    national_outline = gpd.read_file(path, crs='epsg:4326')

    output = output.overlay(national_outline, how='intersection')

    mask = output.area > country['threshold']
    output = output.loc[mask]

    output.to_file(path_out, crs='epsg:4326')


if __name__ == '__main__':

    countries = get_countries()

    for idx, country in tqdm(countries.iterrows(), total=countries.shape[0]):

        if not country['iso3'] in ['MWI', 'GHA']:
            continue

        process_surface_water(country)
