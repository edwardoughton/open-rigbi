"""
Process sites data.

Ed Oughton

February 2022

"""
import sys
import os
import configparser
import pandas as pd
import geopandas as gpd
import pyproj
from shapely.ops import transform
from shapely.geometry import shape, Point, mapping, LineString, MultiPolygon
import rasterio
import random

from misc import get_countries, get_scenarios, get_regions, get_f_curves
from validation import collect, collect_all

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__),'..', 'scripts', 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW = os.path.join(BASE_PATH, 'raw')
DATA_PROCESSED = os.path.join(BASE_PATH, 'processed')


def run_site_processing(region_id):
    """
    Meta function for running site processing.

    """
    iso3 = region_id[:3]
    filename = "{}.csv".format(iso3)
    path = os.path.join(DATA_PROCESSED, iso3, filename)

    country = pd.read_csv(path, encoding='latin-1')
    country = country.to_records('dicts')[0]
    regional_level = int(country['gid_region'])
    gid_level = 'GID_{}'.format(regional_level)

    scenarios = get_scenarios()#[:1]
    regions = get_regions(country, regional_level)#[:1]#[::-1]

    for region in regions:

        if not region[gid_level] == region_id:
           continue

        # print('Working on process_flooding_extent_stats')
        # process_flooding_extent_stats(country, region, scenarios, regional_level)

        # print('Working on query_hazard_layers')
        # query_hazard_layers(country, region, scenarios, regional_level)

        print('Estimating results')
        estimate_results(country, region, scenarios, regional_level)

    #     print('Converting to regional results')
    #     convert_to_regional_results(country, region, scenarios, regional_level)

    # countries = get_countries()
    # scenarios = get_scenarios()
    # collect(countries, scenarios)
    # collect_all(countries)

    return print('Completed processing')


def process_flooding_extent_stats(country, region, scenarios, regional_level):
    """
    Get aggregate statistics on flooding extent by region.

    """
    iso3 = country['iso3']
    name = country['country']
    gid_level = 'GID_{}'.format(regional_level) #regional_level
    region = region[gid_level]

    folder = os.path.join(DATA_PROCESSED, country['iso3'], 'hazards', 'flooding', 'regional')

    for scenario_path in scenarios:#[:1]:

        #if not 'inuncoast_rcp8p5_wtsub_2080_rp1000_0' in scenario_path:
        #    continue

        filename = os.path.basename(scenario_path).replace('.tif','')

        folder_out = os.path.join(DATA_PROCESSED,'results','validation','country_data',
            country['iso3'], 'regional', filename)

        if not os.path.exists(folder_out):
            os.makedirs(folder_out)

        path_out = os.path.join(folder_out, region + '_' + filename + '.csv')

        if os.path.exists(path_out):
            continue

        print('Working on flood extent for {}'.format(filename))

        metrics = []

        path = os.path.join(folder, region + '_' + filename + '.tif')

        if not os.path.exists(path):
            print('path does not exist: {}'.format(path))
            continue

        try:
            raster = rasterio.open(path)
            data = raster.read(1)
        except:
            print('reading failed {}'.format(filename))
            continue

        output = []
        depths = []

        for idx, row in enumerate(data):
            for idx2, i in enumerate(row):
                if i >= 0.000001 and i < 150:
                    coords = raster.transform * (idx2, idx)
                    depths.append(i)
                else:
                    continue

        depths.sort()

        if 'river' in filename:
            hazard = filename.split('_')[0]
            climate_scenario = filename.split('_')[1]
            model = filename.split('_')[2]
            year = filename.split('_')[3]
            return_period = filename.split('_')[4]#[:-4]
            percentile = '-'

        if 'coast' in filename:
            hazard = filename.split('_')[0]
            climate_scenario = filename.split('_')[1]
            model = filename.split('_')[2]
            year = filename.split('_')[3]
            return_period = filename.split('_')[4]
            remaining_portion = filename.split('_')[5]
            if remaining_portion == '0':
                percentile = 0
            else:
                percentile = filename.split('_')[7]#[:-4]

        if len(depths) == 0:
            continue

        metrics.append({
            'hazard': hazard,
            'climate_scenario': climate_scenario,
            'model': model,
            'year': year,
            'return_period': return_period,
            'percentile': percentile,
            'min_depth': round(min(depths),2),
            'mean_depth': sum(depths) / len(depths),
            'median_depth': depths[len(depths)//2],
            'max_depth': max(depths),
            'flooded_area_km2': len(depths),
        })

        metrics = pd.DataFrame(metrics)
        metrics.to_csv(path_out, index=False)

    return


def query_hazard_layers(country, region, scenarios, regional_level):
    """
    Query each hazard layer and estimate fragility.

    """
    iso3 = country['iso3']
    name = country['country']
    gid_level = 'GID_{}'.format(regional_level) #regional_level
    region = region[gid_level]

    filename = 'coastal_lookup.csv'
    folder = os.path.join(DATA_PROCESSED, iso3, 'coastal')
    path_coastal = os.path.join(folder, filename)
    if not os.path.exists(path_coastal):
        coastal_lut = []
    else:
        coastal_lut = pd.read_csv(path_coastal)
        coastal_lut = list(coastal_lut['gid_id'])

    for scenario in scenarios: #tqdm(scenarios):

        scenario_name = os.path.basename(scenario).replace('.tif', '')

        print('Working on {}'.format(scenario_name))

        output = []

        filename = '{}_{}_unique.csv'.format(region, scenario_name)
        folder_out = os.path.join(DATA_PROCESSED, iso3, 'regional_data', region, 'flood_scenarios')
        path_output = os.path.join(folder_out, filename)

        # if os.path.exists(path_output):
        #    continue

        if 'inuncoast' in scenario and region not in coastal_lut:
            print('if inuncoast in scenario and region not in coastal_lut:')
            continue
                
        filename = '{}_{}.tif'.format(region, scenario_name)
        folder_in = os.path.join(DATA_PROCESSED, iso3, 'hazards', 'flooding', 'regional')
        path_in = os.path.join(folder_in, filename)

        filename = '{}_unique.csv'.format(region)
        folder = os.path.join(DATA_PROCESSED, iso3, 'sites', gid_level.lower())
        path_sites = os.path.join(folder, filename)

        if not os.path.exists(path_sites):
            print('path did not exist: {}'.format(path_sites))
            continue

        sites = pd.read_csv(path_sites)#[:5]
        sites = sites.to_dict('records')

        failures = 0

        for site in sites:

            x = float(site['longitude'])
            y = float(site['latitude'])


            with rasterio.open(path_in) as src:

                src.kwargs = {'nodata': -9999}
                    
                coords = [(x, y)]

                depth = [sample[0] for sample in src.sample(coords)][0]

                if depth < 0:
                    depth = 0

                output.append({
                    'radio': site['radio'],
                    # 'mcc': site['mcc'],
                    'net': site['net'],
                    # 'area': site['area'],
                    'cell': site['cell_id'],
                    'latitude': site['latitude'],
                    'longitude': site['longitude'],
                    'gid_level': gid_level,
                    'gid_id': region,
                    'cellid4326': site['cellid4326'],
                    # 'cellid3857': site['cellid3857'],
                    'depth': depth,
                })

        if len(output) == 0:
            return
        print(len(output))
        if not os.path.exists(folder_out):
            os.makedirs(folder_out)

        output = pd.DataFrame(output)

        output.to_csv(path_output, index=False)

    return


def estimate_results(country, region, scenarios, regional_level):
    """

    """
    iso3 = country['iso3']
    name = country['country']
    gid_level = 'GID_{}'.format(regional_level)
    region = region[gid_level]

    # filename = 'fragility_curve.csv'
    # path_fragility = os.path.join(DATA_RAW, filename)
    low, baseline, high = load_f_curves() #path_fragility)

    filename = 'coastal_lookup.csv'
    folder = os.path.join(DATA_PROCESSED, iso3, 'coastal')
    path_coastal = os.path.join(folder, filename)
    if not os.path.exists(path_coastal):
        coastal_lut = []
    else:
        coastal_lut = pd.read_csv(path_coastal)
        coastal_lut = list(coastal_lut['gid_id'])
    print(coastal_lut)
    for scenario in scenarios: #tqdm

        output = []

        scenario_name = os.path.basename(scenario)#[:-4]
        print(scenario_name)
        # if not region == 'EGY.1_1':
        #     continue

        filename = '{}_{}_unique.csv'.format(region, scenario_name)
        folder_out = os.path.join(DATA_PROCESSED, iso3, 'results', 'regional_data', scenario_name)
        path_output = os.path.join(folder_out, filename)

        # if os.path.exists(path_output):
        #     print('path_output exists {}'.format(path_output))
        #     continue

        if 'inuncoast' in scenario and region not in coastal_lut:
            print('if inuncoast in scenario and region not in coastal_lut:')
            continue

        filename = '{}_{}_unique.csv'.format(region, scenario_name)
        folder = os.path.join(DATA_PROCESSED, iso3, 'regional_data', 
                              region, 'flood_scenarios')
        path_in = os.path.join(folder, filename)
        if not os.path.exists(path_in):
            print('path_in does not exist {}'.format(path_in))
            continue
        sites = pd.read_csv(path_in)
        sites = sites.to_dict('records')

        for site in sites:

            if not site['depth'] > 0:
                continue

            damage_low = query_fragility_curve(low, site['depth'])
            damage_baseline = query_fragility_curve(baseline, site['depth'])
            damage_high = query_fragility_curve(high, site['depth'])

            output.append({
                'radio': site['radio'],
                # 'mcc': site['mcc'],
                'net': site['net'],
                # 'area': site['area'],
                'cell': site['cell'],
                'latitude': site['latitude'],
                'longitude': site['longitude'],
                'gid_level': gid_level,
                'gid_id': region,
                'cellid4326': site['cellid4326'],
                # 'cellid3857': site['cellid3857'],
                'depth': site['depth'],
                'damage_low': damage_low,
                'damage_baseline': damage_baseline,
                'damage_high': damage_high,
                'cost_usd_low': round(33333.333 * damage_low),
                'cost_usd_baseline': round(33333.333 * damage_baseline),
                'cost_usd_high': round(33333.333 * damage_high),
            })

        if len(output) == 0:
            continue
        print(len(output))
        if not os.path.exists(folder_out):
            os.makedirs(folder_out)

        output = pd.DataFrame(output)
        output.to_csv(path_output, index=False)

    return


def load_f_curves():
    """
    Load depth-damage curves.

    """
    low = []
    baseline = []
    high = []

    f_curves = get_f_curves()

    for item in f_curves:

        my_dict = {
            'depth_lower_m': item['depth_lower_m'],
            'depth_upper_m': item['depth_upper_m'],
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
        if item['depth_lower_m'] <= depth < item['depth_upper_m']:
            return item['damage']
        else:
            continue

    if depth >= max([d['depth_upper_m'] for d in f_curve]):
        return 1

    print('fragility curve failure: {}'.format(depth))

    return 0


def convert_to_regional_results(country, region, scenarios, regional_level):
    """
    Collect all results.

    """
    scenarios = get_scenarios()[::-1]

    iso3 = country['iso3']
    name = country['country']
    gid_level = 'GID_{}'.format(regional_level)
    region = region[gid_level]

    folder_out = os.path.join(DATA_PROCESSED, iso3, 'results', 'regional_aggregated', 'regions')
    if not os.path.exists(folder_out):
        os.makedirs(folder_out)

    for scenario in scenarios:

        output = []

        scenario_name = os.path.basename(scenario)#[:-4]
        filename = '{}_{}_unique.csv'.format(region, scenario_name)
        path_out = os.path.join(folder_out, filename)

        filename = '{}_{}_unique.csv'.format(region, scenario_name)
        folder_in = os.path.join(DATA_PROCESSED, iso3, 'results',
            'regional_data', scenario_name)
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
        gid_ids = list(data['gid_id'].unique())

        data = data.to_dict('records')

        if len(data) == 0:
            continue

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

            for item in data:

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

    region_id = args[1]

    run_site_processing(region_id)
