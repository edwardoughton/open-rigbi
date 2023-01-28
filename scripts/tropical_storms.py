"""
Process tropical storm data.

"""
import os
import json
import configparser
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.mask import mask
import rasterio.merge
# import glob
# from shapely.geometry import box

from misc import (get_countries, get_scenarios, get_regions,
    remove_small_shapes, get_tropical_storm_scenarios)

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW = os.path.join(BASE_PATH, 'raw')
DATA_PROCESSED = os.path.join(BASE_PATH, 'processed')


def process_tropical_storm_layers(countries, scenario):
    """
    Preprocess tropical storm layers.

    """
    hazard_dir = os.path.join(DATA_RAW, 'storm_data')

    failures = []

    for idx, country in countries.iterrows():

        if not country['iso3'] == 'ARG':
            continue

        iso3 = country['iso3']
        name = country['country']

        filename = os.path.basename(scenario)
        path_in = os.path.join(hazard_dir, filename)

        folder = os.path.join(DATA_PROCESSED, iso3, 'hazards', 'tropical_storm')
        if not os.path.exists(folder):
            os.makedirs(folder)
        path_out = os.path.join(folder, filename)

        if not os.path.exists(path_out):

            print('--{}: {}'.format(name, filename))

            if not os.path.exists(folder):
                os.makedirs(folder)

            # try:
            process_storm_layer(country, path_in, path_out)
            # except:
            #     print('{} failed: {}'.format(country['iso3'], scenario))
            #     failures.append({
            #         'iso3': country['iso3'],
            #         'filename': filename
            #         })
            #     continue
            # print(failures)

    return


def process_storm_layer(country, path_in, path_out):
    """
    Clip the hazard layer to the chosen country boundary
    and place in desired country folder.

    Parameters
    ----------
    country : dict
        Contains all desired country information.
    path_in : string
        The path for the chosen global hazard file to be processed.
    path_out : string
        The path to write the clipped hazard file.

    """
    iso3 = country['iso3']
    regional_level = country['gid_region']

    hazard = rasterio.open(path_in, 'r+', BIGTIFF='YES')
    hazard.nodata = 255
    hazard.crs.from_epsg(4326)

    iso3 = country['iso3']
    path_country = os.path.join(DATA_PROCESSED, iso3,
        'national_outline.shp')

    if os.path.exists(path_country):
        country = gpd.read_file(path_country)
    else:
        print('Must generate national_outline.shp first' )

    #if os.path.exists(path_out):
    #    return

    geo = gpd.GeoDataFrame()

    geo = gpd.GeoDataFrame({'geometry': country['geometry']})

    coords = [json.loads(geo.to_json())['features'][0]['geometry']]

    out_img, out_transform = mask(hazard, coords, crop=True)

    values = set()
    for row in out_img[0]:
        for value in row:
            if not value == 255:
                if not value == 0:
                    values.add(value)
    if len(values) == 0:
        return

    out_meta = hazard.meta.copy()

    out_meta.update({"driver": "GTiff",
                    "height": out_img.shape[1],
                    "width": out_img.shape[2],
                    "transform": out_transform,
                    "crs": 'epsg:4326'})

    with rasterio.open(path_out, "w", **out_meta) as dest:
            dest.write(out_img)

    return


def process_regional_storm_layers(countries, scenario):
    """
    Process each storm layer at the regional level.

    """

    for idx, country in countries.iterrows():

        # if not country['iso3'] == 'GBR':
        #     continue

        iso3 = country['iso3']
        name = country['country']
        regional_level = country['gid_region']

        hazard_dir = os.path.join(DATA_PROCESSED, iso3, 'hazards', 'tropical_storm')
        filename = os.path.basename(scenario)
        path_in = os.path.join(hazard_dir, filename)

        folder = os.path.join(DATA_PROCESSED, iso3, 'hazards', 'tropical_storm', 'regional')
        if not os.path.exists(folder):
            os.makedirs(folder)

        regions = get_regions(country, regional_level)

        for idx, region_series in regions.iterrows():

            region = region_series['GID_{}'.format(regional_level)]
            path_out = os.path.join(folder, region + '_' + filename)

            # if not region == 'GBR.1.69_1':
            #     continue

            if not os.path.exists(path_out):

                print('--{}: {}'.format(name, filename))

                #if not os.path.exists(folder):
                #    os.makedirs(folder)
                #try:
                process_regional_storm_layer(country, region, path_in, path_out)
                #except:
                #print('{} failed: {}'.format(country['iso3'], scenario))
                #    continue

            # #failures.append({
            #     #     'iso3': iso3,
            #     #     'filename': filename
            #     # })

    return


def process_regional_storm_layer(country, region, path_in, path_out):
    """
    Clip the hazard layer to the chosen country boundary
    and place in desired country folder.

    Parameters
    ----------
    country : dict
        Contains all desired country information.
    path_in : string
        The path for the chosen global hazard file to be processed.
    path_out : string
        The path to write the clipped hazard file.

    """
    iso3 = country['iso3']
    regional_level = country['gid_region']
    gid_level = 'GID_{}'.format(regional_level)

    hazard = rasterio.open(path_in, 'r+', BIGTIFF='YES')
    hazard.nodata = 255
    hazard.crs.from_epsg(4326)

    iso3 = country['iso3']
    filename = 'regions_{}_{}.shp'.format(regional_level, iso3)
    path_country = os.path.join(DATA_PROCESSED, iso3, 'regions', filename)

    if os.path.exists(path_country):
        regions = gpd.read_file(path_country)
        region = regions[regions[gid_level] == region]
    else:
        print('Must generate national_outline.shp first' )
        return

    geo = gpd.GeoDataFrame()

    geo = gpd.GeoDataFrame({'geometry': region['geometry']})

    coords = [json.loads(geo.to_json())['features'][0]['geometry']]

    out_img, out_transform = mask(hazard, coords, crop=True)

    values = set()
    for row in out_img[0]:
        for value in row:
            if not value == 255:
                if not value == 0:
                    values.add(value)
    if len(values) == 0:
        return

    out_meta = hazard.meta.copy()

    out_meta.update({"driver": "GTiff",
                    "height": out_img.shape[1],
                    "width": out_img.shape[2],
                    "transform": out_transform,
                    "crs": 'epsg:4326'})

    with rasterio.open(path_out, "w", **out_meta) as dest:
            dest.write(out_img)

    return


if __name__ == "__main__":

    scenarios = get_tropical_storm_scenarios()#[:1]
    countries = get_countries()

    for scenario in scenarios:

        process_tropical_storm_layers(countries, scenario)

        process_regional_storm_layers(countries, scenario)
