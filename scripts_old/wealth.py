"""
Process provert layer.

Written by Ed Oughton.

July 2022

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

from misc import get_countries

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW = os.path.join(BASE_PATH, 'raw')
DATA_PROCESSED = os.path.join(BASE_PATH, 'processed')


def create_regional_grid(country):
    """
    Create a grid at the desired resolution for each region.

    """
    filename = "national_outline.shp"
    folder = os.path.join(DATA_PROCESSED, country['iso3'])
    path = os.path.join(folder, filename)

    national_outline = gpd.read_file(path, crs='epsg:4326')
    national_outline = national_outline.to_crs(3857)

    xmin, ymin, xmax, ymax= national_outline.total_bounds

    cell_size = 2400

    grid_cells = []
    for x0 in np.arange(xmin, xmax+cell_size, cell_size ):
        for y0 in np.arange(ymin, ymax+cell_size, cell_size):
            x1 = x0 - cell_size
            y1 = y0 + cell_size
            grid_cells.append(box(x0, y0, x1, y1))

    grid = gpd.GeoDataFrame(grid_cells, columns=['geometry'], crs='epsg:3857')

    grid = grid.overlay(national_outline, how='intersection')

    grid = grid.to_crs(4326)

    filename = 'regions_{}_{}.shp'.format(country['lowest'], country['iso3'])
    folder = os.path.join(DATA_PROCESSED, country['iso3'], 'regions')
    path_in = os.path.join(folder, filename)
    regions = gpd.read_file(path_in, crs='epsg:4326')#[:3]

    folder = os.path.join(DATA_PROCESSED, country['iso3'], 'relative_wealth_index', 'grid')
    if not os.path.exists(folder):
        os.makedirs(folder)

    for idx, region in regions.iterrows():

        gid_level = 'GID_{}'.format(country['lowest'])
        gid_id = region[gid_level]

        output = []

        for idx, grid_tile in grid.iterrows():
            if region['geometry'].intersects(grid_tile['geometry'].centroid):
                output.append({
                    'geometry': grid_tile['geometry'],
                    'properties': {
                        'tile_id': idx,
                    }
                })

        if len(output) == 0:
            continue

        output = gpd.GeoDataFrame.from_features(output, crs='epsg:4326')

        filename = "{}.shp".format(gid_id)
        path_out = os.path.join(folder, filename)
        output.to_file(path_out, crs='epsg:4326')

    return


def process_regional_wealth(country):
    """
    Process wealth index by country.

    """
    filename = "{}_relative_wealth_index.csv".format(country['iso3'])
    folder = os.path.join(DATA_RAW, 'relative_wealth_index')
    path_in = os.path.join(folder, filename)

    folder_out = os.path.join(DATA_PROCESSED, country['iso3'], 'relative_wealth_index', 'regions')

    if not os.path.exists(folder_out):
        os.makedirs(folder_out)

    data = pd.read_csv(path_in)#[:10]
    data['decile'] = pd.qcut(data['rwi'], 5, labels=False)
    data = gpd.GeoDataFrame(data,
            geometry=gpd.points_from_xy(data.longitude, data.latitude),
            crs='epsg:4326')
    data = data.drop(columns=['longitude', 'latitude'])

    filename = 'regions_{}_{}.shp'.format(country['lowest'], country['iso3'])
    folder = os.path.join(DATA_PROCESSED, country['iso3'], 'regions')
    path_in = os.path.join(folder, filename)
    regions = gpd.read_file(path_in, crs='epsg:4326')#[:3]

    for idx, region in regions.iterrows():

        output = []

        gid_level = 'GID_{}'.format(country['lowest'])
        gid_id = region[gid_level]

        for idx, point in data.iterrows():
            if point['geometry'].intersects(region['geometry']):
                output.append({
                    'geometry': point['geometry'],
                    'properties': {
                        'rwi': point['rwi'],
                        'decile': point['decile'],
                    }
                })

        if len(output) == 0:
            continue

        output = gpd.GeoDataFrame.from_features(output, crs='epsg:4326')

        filename = "{}.shp".format(gid_id)
        path_out = os.path.join(folder_out, filename)
        output.to_file(path_out, crs='epsg:4326')

    return


def export_wealth_grid(country):
    """
    Process wealth index by country.

    """
    output = []

    filename = 'regions_{}_{}.shp'.format(country['lowest'], country['iso3'])
    folder = os.path.join(DATA_PROCESSED, country['iso3'], 'regions')
    path_in = os.path.join(folder, filename)
    regions = gpd.read_file(path_in, crs='epsg:4326')#[:2]

    folder_regions = os.path.join(DATA_PROCESSED, country['iso3'], 'relative_wealth_index', 'regions')
    folder_grid = os.path.join(DATA_PROCESSED, country['iso3'], 'relative_wealth_index', 'grid')

    for idx, region in regions.iterrows():

        gid_level = 'GID_{}'.format(country['lowest'])
        gid_id = region[gid_level]

        path1 = os.path.join(folder_regions, gid_id + '.shp')
        if not os.path.exists(path1):
            continue
        points = gpd.read_file(path1, crs='epsg:4326')

        path2 = os.path.join(folder_grid, gid_id + '.shp')
        if not os.path.exists(path2):
            continue
        grid = gpd.read_file(path2, crs='epsg:4326')

        for idx, point in points.iterrows():
            for idx, grid_tile in grid.iterrows():
                if point['geometry'].intersects(grid_tile['geometry']):
                    output.append({
                        'geometry': grid_tile['geometry'],
                        'properties': {
                            'rwi': point['rwi'],
                            'decile': point['decile'],
                        }
                    })

    output = gpd.GeoDataFrame.from_features(output, crs='epsg:4326')

    if len(output) == 0:
        return

    filename = "rwi_grid.shp"
    path_out = os.path.join(folder_regions, '..', filename)
    output.to_file(path_out, crs='epsg:4326')

    return


def separate_bottom_portion(country):
    """
    Writes out bottom 40% of areas based on relative wealth.

    """
    filename = "rwi_grid.shp"
    folder = os.path.join(DATA_PROCESSED, country['iso3'], 'relative_wealth_index')
    path_in = os.path.join(folder, filename)
    grid = gpd.read_file(path_in, crs='epsg:4326')#[:2]

    quintile_0 = grid[grid['decile'].isin([0,1]) ]
    filename = "bottom_40_perc.shp"
    path_out = os.path.join(folder, filename)
    quintile_0.to_file(path_out, crs='epsg:4326')

    return


if __name__ == '__main__':

    countries = get_countries()

    for idx, country in tqdm(countries.iterrows(), total=countries.shape[0]):

        if not country['iso3'] in ['MWI', 'GHA']:
            continue

        create_regional_grid(country)

        process_regional_wealth(country)

        export_wealth_grid(country)

        separate_bottom_portion(country)
