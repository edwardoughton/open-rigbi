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

        if not country['iso3'] == 'USA':
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

        if not country['iso3'] == 'USA':
            continue

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

        if not country['iso3'] == 'USA':
            continue

        iso3 = country['iso3']
        name = country['country']
        regional_level = int(country['gid_region'])
        gid_level = 'GID_{}'.format(regional_level) #regional_level

        print('Working on {}'.format(iso3))

        regions = get_regions(country, regional_level)

        if len(regions) == 0:
            print('get_regions returned no data')
            continue

        for idx, region_series in regions.iterrows():

            region = region_series['GID_{}'.format(regional_level)]

            #if not region == 'GBR.1.20_1':
            #    continue

            output = []

            filename = '{}_{}.csv'.format(region, os.path.basename(scenario).replace('.tif',''))
            folder_out = os.path.join(DATA_PROCESSED, iso3, 'regional_data', region, 'tropical_storm_scenarios')
            if not os.path.exists(folder_out):
                os.makedirs(folder_out)
            path_output = os.path.join(folder_out, filename)

            if os.path.exists(path_output):
                print('output file already exists: {}'.format(path_output))
                continue

            filename = '{}.csv'.format(region)
            folder = os.path.join(DATA_PROCESSED, iso3, 'sites', gid_level.lower())
            path = os.path.join(folder, filename)

            if not os.path.exists(path):
                print('sites file does not exist: {}'.format(path))
                continue

            filename = os.path.join(region + '_' + scenario.replace('.tif','') + '.tif')
            scenario_path = os.path.join(DATA_PROCESSED,iso3,'hazards','tropical_storm','regional',filename)

            if not os.path.exists(scenario_path):
                print('scenario_path does not exist: {}'.format(scenario_path))
                continue

            sites = pd.read_csv(path)#[:10]

            failures = 0

            for idx, site in sites.iterrows():

                x = float(site['cellid4326'].split('_')[0])
                y = float(site['cellid4326'].split('_')[1])

                with rasterio.open(scenario_path) as src:

                    src.kwargs = {'nodata':255}

                    coords = [(x, y)]

                    wind_speed = [sample[0] for sample in src.sample(coords)][0]

                    if wind_speed == 255:
                        wind_speed = 0

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


def estimate_results(countries, scenario):
    """

    """
    scenario = scenario.replace('.tif', '')

    filename = 'fragility_curve_tropical_storm.csv'
    path_fragility = os.path.join(DATA_RAW, filename)
    low, baseline, high = load_f_curves(path_fragility)

    for idx, country in countries.iterrows():

        # if not country['iso3'] == 'GBR':
        #     continue

        iso3 = country['iso3']
        name = country['country']
        regional_level = int(country['gid_region'])
        gid_level = 'GID_{}'.format(regional_level) #regional_level

        print('Working on {}'.format(iso3))

        regions = get_regions(country, regional_level)

        if len(regions) == 0:
            print('get_regions returned no data')
            continue

        for idx, region_series in regions.iterrows():

            region = region_series['GID_{}'.format(regional_level)]

            # if not region == 'GBR.1.20_1':
            #     continue

            output = []

            filename = '{}_{}.csv'.format(region, scenario)
            folder_out = os.path.join(DATA_PROCESSED, iso3, 'results', 'regional_data', scenario)
            path_output = os.path.join(folder_out, filename)

            #if os.path.exists(path_output):
                #print('path_output exists {}'.format(path_output))
            #    continue

            filename = '{}_{}.csv'.format(region, scenario)
            folder = os.path.join(DATA_PROCESSED, iso3, 'regional_data', region, 'tropical_storm_scenarios')
            path_in = os.path.join(folder, filename)
            if not os.path.exists(path_in):
                # print('path_in does not exist {}'.format(path_in))
                continue
            sites = pd.read_csv(path_in)

            for idx, site in sites.iterrows():

                if not site['wind_speed'] > 0:
                    continue

                damage_low = query_fragility_curve(low, site['wind_speed'])
                damage_baseline = query_fragility_curve(baseline, site['wind_speed'])
                damage_high = query_fragility_curve(high, site['wind_speed'])

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
                    'wind_speed': site['wind_speed'],
                    'damage_low': damage_low,
                    'damage_baseline': damage_baseline,
                    'damage_high': damage_high,
                    'cost_usd_low': round(40000 * damage_low),
                    'cost_usd_baseline': round(40000 * damage_baseline),
                    'cost_usd_high': round(40000 * damage_high),
                })

            if len(output) == 0:
                #print('len(output) == 0')
                continue

            if not os.path.exists(folder_out):
                os.makedirs(folder_out)

            output = pd.DataFrame(output)
            output.to_csv(path_output, index=False)

    return


def load_f_curves(path_fragility):
    """
    Load depth-damage curves.

    """
    low = []
    baseline = []
    high = []

    f_curves = pd.read_csv(path_fragility)

    for idx, item in f_curves.iterrows():

        my_dict = {
            'wind_speed_lower_m': item['wind_speed_lower_m'],
            'wind_speed_upper_m': item['wind_speed_upper_m'],
            'damage': item['damage'],
        }

        if item['scenario'] == 'low':
            low.append(my_dict)
        elif item['scenario'] == 'baseline':
            baseline.append(my_dict)
        elif item['scenario'] == 'high':
            high.append(my_dict)

    return low, baseline, high


def query_fragility_curve(f_curve, depth):
    """
    Query the fragility curve.

    """
    if depth < 0:
        return 0

    for item in f_curve:
        if item['wind_speed_lower_m'] <= depth < item['wind_speed_upper_m']:
            return item['damage']
        else:
            continue

    if depth >= max([d['wind_speed_upper_m'] for d in f_curve]):
        return 1

    print('fragility curve failure: {}'.format(depth))

    return 0


def convert_to_regional_results(countries, scenario):
    """
    Collect all results.

    """
    scenario = scenario.replace('.tif', '')

    for idx, country in countries.iterrows():

        # if not country['iso3'] == 'GBR':
        #     continue

        iso3 = country['iso3']
        name = country['country']
        regional_level = int(country['gid_region'])
        gid_level = 'GID_{}'.format(regional_level) #regional_level

        print('Working on {}'.format(iso3))

        regions = get_regions(country, regional_level)

        if len(regions) == 0:
            print('get_regions returned no data')
            continue

        for idx, region_series in regions.iterrows():

            region = region_series['GID_{}'.format(regional_level)]

            # if not region == 'GBR.1.20_1':
            #     continue

            output = []

            folder_out = os.path.join(DATA_PROCESSED, iso3, 'results', 'regional_aggregated', 'regions')
            if not os.path.exists(folder_out):
                os.makedirs(folder_out)

            filename = '{}_{}.csv'.format(region, scenario)
            path_out = os.path.join(folder_out, filename)

            filename = '{}_{}.csv'.format(region, scenario)
            folder_in = os.path.join(DATA_PROCESSED, iso3, 'results',
                'regional_data', scenario)
            path_in = os.path.join(folder_in, filename)

            if not os.path.exists(path_in):
                output.append({
                        'iso3': country['iso3'],
                        'iso2': country['iso2'],
                        'country': country['country'],
                        'continent': country['continent'],
                        'gid_level': 'NA',
                        'gid_id': 'NA',
                        'radio': 'NA',
                        'network': 'NA',
                        'cell_count_low': 0,
                        'cell_count_baseline': 0,
                        'cell_count_high': 0,
                        'cost_usd_low': 0,
                        'cost_usd_baseline': 0,
                        'cost_usd_high': 0,
                    })
                continue

            data = pd.read_csv(path_in, sep=',')

            if len(data) == 0:
                continue

            gid_ids = list(data['gid_id'].unique())
            # radios = list(data['radio'].unique())
            # networks = list(data['net'].unique())

            for gid_id in gid_ids:

                #for network in networks:

                cell_count_low = 0
                cell_count_baseline = 0
                cell_count_high = 0
                cost_usd_low = 0
                cost_usd_baseline = 0
                cost_usd_high = 0

                for idx, item in data.iterrows():

                    if not item['gid_id'] == gid_id:
                        continue

                    if item['cost_usd_low'] > 0:
                        cell_count_low += 1
                        cost_usd_low += item['cost_usd_low']

                    if item['cost_usd_baseline'] > 0:
                        cell_count_baseline += 1
                        cost_usd_baseline += item['cost_usd_baseline']

                    if item['cost_usd_high'] > 0:
                        cell_count_high += 1
                        cost_usd_high += item['cost_usd_high']

                output.append({
                    'iso3': country['iso3'],
                    'iso2': country['iso2'],
                    'country': country['country'],
                    'continent': country['continent'],
                    'gid_level': item['gid_level'],
                    'gid_id': gid_id,
                    'cell_count_low': cell_count_low,
                    'cost_usd_low': cost_usd_low,
                    'cell_count_baseline': cell_count_baseline,
                    'cost_usd_baseline': cost_usd_baseline,
                    'cell_count_high': cell_count_high,
                    'cost_usd_high': cost_usd_high,
                    })

            if len(output) == 0:
                continue

            output = pd.DataFrame(output)

            output.to_csv(path_out, index=False)

    return


if __name__ == "__main__":

    args = sys.argv

    scenario = args[1]

    countries = get_countries()

    # process_tropical_storm_layers(countries, scenario)
    # process_regional_storm_layers(countries, scenario)
    # query_tropical_storm_layers(countries, scenario)
    # estimate_results(countries, scenario)

    convert_to_regional_results(countries, scenario)

    # countries = get_countries()
    # scenarios = get_tropical_storm_scenarios()#[:1]

    # for scenario in scenarios:

    #     # process_tropical_storm_layers(countries, scenario)

    #     # process_regional_storm_layers(countries, scenario)

    #     query_tropical_storm_layers(countries, scenario)
