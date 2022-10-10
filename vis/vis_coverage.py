"""
Visualize coverage of cell sites.

Written by Ed Oughton.

May 2022.

"""
import os
import sys
import configparser
# import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
# import seaborn as sns
import contextily as cx
# import geopy as gp
# from math import ceil
from tqdm import tqdm

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), '..', 'scripts', 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW = os.path.join(BASE_PATH, 'raw')
DATA_PROCESSED = os.path.join(BASE_PATH, 'processed')
RESULTS = os.path.join(BASE_PATH, '..', 'results')
VIS = os.path.join(BASE_PATH, '..', 'vis', 'figures')
REPORTS = os.path.join(BASE_PATH, '..', 'reports', 'images')

sys.path.insert(1, os.path.join(BASE_PATH, '..','scripts'))
from misc import get_countries, get_regions


def get_grid_tiles(country):
    """
    Return country grid tiles.

    """

    filename = 'grid.shp'
    folder = os.path.join(DATA_RAW, 'gridded_gdp', 'grid')
    path = os.path.join(folder, filename)

    grid = gpd.read_file(path, crs='epsg:4326')

    grid = grid[grid.ISO3 == country['iso3']]

    return grid


def find_coverage(regions, grid, gid_level, path_out):
    """

    """

    output = []

    for idx, region in regions.iterrows():

        gdf = gpd.GeoDataFrame(geometry=gpd.GeoSeries(region['geometry']), crs='epsg:4326')
        try:
            grid_tiles = gpd.overlay(gdf, grid, how='intersection')
        except:
            continue

        gid_id = region['GID_{}'.format(gid_level)]

        filename = '{}.shp'.format(gid_id)
        folder = os.path.join(DATA_PROCESSED, country['iso3'], 'sites', 'regional_sites')
        path = os.path.join(folder, filename)

        if os.path.exists(path):
            sites = gpd.read_file(path, crs='epsg:4326')
        else:
            sites = []
            # coverage = 'No Coverage'

        for idx, grid_tile in grid_tiles.iterrows():

            # if not grid_tile['gID'] == 40995:
            #     continue

            if len(sites) > 0:

                gdf = gpd.GeoDataFrame(geometry=gpd.GeoSeries(grid_tile['geometry']), crs='epsg:4326')

                try:
                    sites_subset = gpd.overlay(gdf, sites, how='intersection', keep_geom_type=False)
                except:
                    sites_subset = []

            else:
                sites_subset = []

            if len(sites_subset) > 0:

                technologies = sites_subset['radio'].unique()

                if 'LTE' in technologies:
                    coverage = 'LTE'
                elif 'UMTS' in technologies:
                    coverage = 'UMTS'
                elif 'GSM' in technologies:
                    coverage = 'GSM'
                else:
                    coverage = 'No Coverage'
            else:
                coverage = 'No Coverage'

            output.append({
                'type': 'Polygon',
                'geometry': grid_tile['geometry'],
                'properties': {
                    'gID': grid_tile['gID'],
                    'ISO3': grid_tile['ISO3'],
                    'px': grid_tile['px'],
                    'py': grid_tile['py'],
                    'coverage': coverage,
                    'gid_id': gid_id,
                }
            })

    if len(output) == 0:
        return

    output = gpd.GeoDataFrame.from_features(output, crs='epsg:4326')

    output.to_file(path_out, crs='epsg:4326')

    return


def visualize(countries):
    """
    Visualize county coverage.

    """
    output = []

    for idx, country in countries.iterrows():

        # if not country['iso3'] == 'SSD':
        #     continue

        if not country['continent'] == 'Africa':
            continue

        filename = 'coverage_grid.shp'
        path_data = os.path.join(DATA_PROCESSED, country['iso3'], 'coverage', filename)
        if not os.path.exists(path_data):
            continue

        data = gpd.read_file(path_data,crs='epsg:4326')

        for idx, item in data.iterrows():
            output.append({
                'geometry': item['geometry'],
                'properties': {
                    'coverage': item['coverage']
                }
            })

    output = gpd.GeoDataFrame.from_features(output, crs='epsg:4326')

    output['coverage'] = output['coverage'].replace(['GSM'], '2G')
    output['coverage'] = output['coverage'].replace(['UMTS'], '3G')
    output['coverage'] = output['coverage'].replace(['LTE'], '4G')
    # output['coverage'] = output['coverage'].replace(['GSM'], '2G')

    fig, ax = plt.subplots(1, 1, figsize=(10,8))
    output.plot(column='coverage', categorical=True, ax=ax, cmap='viridis_r',
        linewidth=0.2, alpha=0.8, legend=True, edgecolor='grey')

    cx.add_basemap(ax, crs='epsg:4326')

    ssd = gpd.read_file(os.path.join(DATA_PROCESSED, 'SSD', 'national_outline.shp'), crs='epsg:4326')
    esh = gpd.read_file(os.path.join(DATA_PROCESSED, 'ESH', 'national_outline.shp'), crs='epsg:4326')

    ssd.plot(color='grey', ax=ax, linewidth=0.2, alpha=0.8, edgecolor='grey')
    esh.plot(color='grey', ax=ax, linewidth=0.2, alpha=0.8, edgecolor='grey')

    name = 'Mobile Infrastructure Coverage (n={})'.format(len(output))
    fig.suptitle(name)

    path = os.path.join(VIS, 'Coverage.tiff')
    fig.tight_layout()
    fig.savefig(path, dpi=600)

    plt.close(fig)


if __name__ == '__main__':

    gid_level = 1

    countries = get_countries()

    for idx, country in tqdm(countries.iterrows(), total=countries.shape[0]):

        # if not country['iso3'] == 'SSD':
        #     continue

        # if not country['continent'] == 'Africa':
        #     continue

        folder = os.path.join(DATA_PROCESSED, country['iso3'], 'coverage')
        if not os.path.exists(folder):
            os.mkdir(folder)
        filename = 'coverage_grid.shp'
        path_out = os.path.join(folder, filename)

        if os.path.exists(path_out):
            continue

        print('-Working on {}'.format(country['country']))

        regions = get_regions(country, gid_level)

        if len(regions) == 0:
            continue

        grid = get_grid_tiles(country)

        find_coverage(regions, grid, gid_level, path_out)

    visualize(countries)
