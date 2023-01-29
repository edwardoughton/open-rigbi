"""
Process tropical storm data.

"""
import sys
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

        #if not country['iso3'] == 'ARG':
        #    continue

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

            try:
                process_storm_layer(country, path_in, path_out)
            except:
                print('{} failed: {}'.format(country['iso3'], scenario))
            #     failures.append({
            #         'iso3': country['iso3'],
            #         'filename': filename
            #         })
                continue
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
        return

    if os.path.exists(path_out):
        return

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

        if len(regions) == 0:
            continue

        for idx, region_series in regions.iterrows():

            region = region_series['GID_{}'.format(regional_level)]
            path_out = os.path.join(folder, region + '_' + filename)

            # if not region == 'GBR.1.69_1':
            #     continue

            if not os.path.exists(path_out):

                print('--{}: {}'.format(name, filename))

                #if not os.path.exists(folder):
                #    os.makedirs(folder)
                try:
                    process_regional_storm_layer(country, region, path_in, path_out)
                except:
                    print('{} failed: {}'.format(country['iso3'], scenario))
                    continue

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

    if os.path.exists(path_out):
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


def query_tropical_storm_layers(countries, scenario):
    """
    Query tropical storm hazard layers and estimate damage.

    """
    for idx, country in countries.iterrows():

        # if not country['iso3'] == 'GBR':
        #     continue

        iso3 = country['iso3']
        name = country['country']
        regional_level = int(country['gid_region'])
        gid_level = 'GID_{}'.format(regional_level) #regional_level

        print('Working on {}'.format(iso3))

        regions = get_regions(country, regional_level)

        for idx, region_series in regions.iterrows():

            region = region_series['GID_{}'.format(regional_level)]

            # if not region == 'GBR.1.20_1':
            #     continue

            output = []

            filename = '{}_{}.csv'.format(region, os.path.basename(scenario).replace('.tif',''))
            folder_out = os.path.join(DATA_PROCESSED, iso3, 'regional_data', region, 'tropical_storm_scenarios')
            if not os.path.exists(folder_out):
                os.makedirs(folder_out)
            path_output = os.path.join(folder_out, filename)

            # if os.path.exists(path_output):
            #     continue

            filename = '{}.csv'.format(region)
            folder = os.path.join(DATA_PROCESSED, iso3, 'sites', gid_level.lower())
            path = os.path.join(folder, filename)

            if not os.path.exists(path):
                continue

            sites = pd.read_csv(path)#[:10]

            failures = 0

            for idx, site in sites.iterrows():

                x = float(site['cellid4326'].split('_')[0])
                y = float(site['cellid4326'].split('_')[1])

                with rasterio.open(scenario) as src:

                    src.kwargs = {'nodata':255}

                    coords = [(x, y)]

                    wind_speed = [sample[0] for sample in src.sample(coords)][0]

                    output.append({
                        'radio': site['radio'],
                        'mcc': site['mcc'],
                        'net': site['net'],
                        'area': site['area'],
                        'cell': site['cell'],
                        'gid_level': gid_level,
                        'gid_id': region,
                        'cellid4326': site['cellid4326'],
                        'cellid3857': site['cellid3857'],
                        'wind_speed': wind_speed,
                    })

            if len(output) == 0:
                return

            if not os.path.exists(folder_out):
                os.makedirs(folder_out)

            output = pd.DataFrame(output)

            output.to_csv(path_output, index=False)

    return


if __name__ == "__main__":

    args = sys.argv

    scenario = args[1]

    countries = get_countries()

    query_tropical_storm_layers(countries, scenario)



    # countries = get_countries()
    # scenarios = get_tropical_storm_scenarios()#[:1]

    # for scenario in scenarios:

    #     # process_tropical_storm_layers(countries, scenario)

    #     # process_regional_storm_layers(countries, scenario)

    #     query_tropical_storm_layers(countries, scenario)

