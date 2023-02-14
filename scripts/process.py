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

from misc import get_countries, get_scenarios, get_regions

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__),'..', 'scripts', 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW = os.path.join(BASE_PATH, 'raw')
DATA_PROCESSED = os.path.join(BASE_PATH, 'processed')


def run_site_processing(iso3):
    """
    Meta function for running site processing.

    """
    filename = "countries.csv"
    path = os.path.join(DATA_RAW, filename)

    countries = pd.read_csv(path, encoding='latin-1')
    country = countries[countries.iso3 == iso3]
    country = country.to_records('dicts')[0]
    regional_level = int(country['gid_region'])

    scenarios = get_scenarios()
    regions_df = get_regions(country, regional_level)#[:1]#[::-1]

    for idx, region in regions_df.iterrows():

        # print('Working on process_flooding_extent_stats')
        # process_flooding_extent_stats(country, region, scenarios)

        print('Working on query_hazard_layers')
        query_hazard_layers(country, region, scenarios, regional_level)

        print('Estimating results')
        estimate_results(country, region, scenarios, regional_level)

        print('Converting to regional results')
        convert_to_regional_results(country, region, scenarios)

    return print('Completed processing')


def process_flooding_extent_stats(country, region, scenarios):
    """
    Get aggregate statistics on flooding extent by region.

    """
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
                if i > 0.001 and i < 150:
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

    for scenario in scenarios: #tqdm(scenarios):

        print('Working on {}'.format(scenario))

        output = []

        gid_id = region #region[gid_level]
        scenario_name = os.path.basename(scenario).replace('.tif', '')

        filename = '{}_{}.csv'.format(gid_id, scenario_name)
        folder_out = os.path.join(DATA_PROCESSED, iso3, 'regional_data', gid_id, 'flood_scenarios')
        path_output = os.path.join(folder_out, filename)

        if os.path.exists(path_output):
           continue

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

                depth = [sample[0] for sample in src.sample(coords)][0]

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
                    'depth': depth,
                })

        if len(output) == 0:
            return

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

    filename = 'fragility_curve.csv'
    path_fragility = os.path.join(DATA_RAW, filename)
    low, baseline, high = load_f_curves(path_fragility)

    for scenario in scenarios: #tqdm

        output = []

        gid_id = region#[gid_level]
        scenario_name = os.path.basename(scenario)[:-4]
        print(scenario_name)
        # if not gid_id == 'EGY.1_1':
        #     continue

        filename = '{}_{}.csv'.format(gid_id, scenario_name)
        folder_out = os.path.join(DATA_PROCESSED, iso3, 'results', 'regional_data', scenario_name)
        path_output = os.path.join(folder_out, filename)

        #if os.path.exists(path_output):
            #print('path_output exists {}'.format(path_output))
        #    continue

        filename = '{}_{}.csv'.format(gid_id, scenario_name)
        folder = os.path.join(DATA_PROCESSED, iso3, 'regional_data', gid_id, 'flood_scenarios')
        path_in = os.path.join(folder, filename)
        if not os.path.exists(path_in):
            # print('path_in does not exist {}'.format(path_in))
            continue
        sites = pd.read_csv(path_in)

        for idx, site in sites.iterrows():

            if not site['depth'] > 0:
                continue

            damage_low = query_fragility_curve(low, site['depth'])
            damage_baseline = query_fragility_curve(baseline, site['depth'])
            damage_high = query_fragility_curve(high, site['depth'])

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
                'depth': site['depth'],
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


def convert_to_regional_results(country, region, scenarios):
    """
    Collect all results.

    """
    scenarios = get_scenarios()[::-1]

    iso3 = region[:3]

    folder_out = os.path.join(DATA_PROCESSED, iso3, 'results', 'regional_aggregated', 'regions')
    if not os.path.exists(folder_out):
        os.mkdir(folder_out)

    for scenario in scenarios:

        output = []

        scenario_name = os.path.basename(scenario)[:-4]
        filename = '{}_{}.csv'.format(region, scenario_name)
        path_out = os.path.join(folder_out, filename)

        filename = '{}_{}.csv'.format(region, scenario_name)
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


def collect_final_results(collection_type):
    """
    Collect all results.

    """
    scenarios = get_scenarios()[::-1]
    countries = get_countries()

    folder_out = os.path.join(DATA_PROCESSED, 'results')
    if not os.path.exists(folder_out):
        os.mkdir(folder_out)

    for scenario in scenarios:

        output = []

        scenario_name = os.path.basename(scenario)[:-4]

        path_out = os.path.join(folder_out, scenario_name + '.csv')

        for idx, country in countries.iterrows():

            if not collection_type == 'all':
                if not country['iso3'] == collection_type:
                    continue

            collect_national_results(country['iso3'], scenario)

            path = os.path.join(DATA_PROCESSED, country['iso3'], 'results',
                'national_data', scenario_name + '.csv')

            if not os.path.exists(path):
                output.append({
                        'iso3': country['iso3'],
                        'iso2': country['iso2'],
                        'country': country['country'],
                        'continent': country['continent'],
                        'radio': 'NA',
                        'network': 'NA',
                        'cell_count': 0,
                        'cost_usd': 0,
                    })
                continue

            # print(path)
            data = pd.read_csv(path, sep=',')
            # print(data.columns)
            if len(data) == 0:
                continue

            radios = list(data['radio'].unique())
            networks = list(data['net'].unique())

            for radio in radios:

                #for network in networks:

                cell_count = 0
                cost_usd = 0

                for idx, item in data.iterrows():

                    if not item['radio'] == radio:
                        continue

                #        if not item['net'] == network:
                #            continue

                    if not item['failure'] == 1:
                        continue
                    # print(cell_count)
                    cell_count += 1
                    cost_usd += item['cost_usd']

                output.append({
                    'iso3': country['iso3'],
                    'iso2': country['iso2'],
                    'country': country['country'],
                    'continent': country['continent'],
                    'radio': radio,
                    #'network': network,
                    'cell_count': cell_count,
                    'cost_usd': cost_usd,
                    })

        if len(output) == 0:
            # print('output len = 0')
            continue

        output = pd.DataFrame(output)

        output.to_csv(path_out, index=False)

    return


def collect_national_results(iso3, scenario):
    """
    Collect regional results and write to national results folder.

    """
    output = []

    scenario_name = os.path.basename(scenario)[:-4]
    #print('collecting national results for {}'.format(scenario_name))
    folder = os.path.join(DATA_PROCESSED, iso3, 'results', 'regional_data', scenario_name)

    if not os.path.exists(folder):
        #print('collect_national_results: folder does not exist: {}'.format(folder))
        return

    all_regional_results = os.listdir(folder)

    if len(all_regional_results) == 0:
        #print('len of all_regional_results = 0')
        return

    for filename in all_regional_results:

        path_in = os.path.join(folder, filename)

        if not os.path.exists(path_in):
            continue
        try:
            data = pd.read_csv(path_in)
            data = data.to_dict('records')
            output = output + data
        except:
            print('failed on {})'.format(path_in))

    if len(output) == 0:
        #print('2. len of output = 0')
        return

    output = pd.DataFrame(output)

    folder_out = os.path.join(DATA_PROCESSED, iso3, 'results', 'national_data')
    if not os.path.exists(folder_out):
        print('folder out did not exist')
        os.mkdir(folder_out)
    path_out = os.path.join(folder_out, scenario_name + '.csv')
    output.to_csv(path_out, index=False)

    return


def collect_regional_results(collection_type):
    """
    Collect all results.

    """
    scenarios = get_scenarios()[::-1]
    countries = get_countries()

    folder_out = os.path.join(DATA_PROCESSED, 'results', 'regional')
    if not os.path.exists(folder_out):
        os.mkdir(folder_out)

    for scenario in scenarios:

        if not 'rcp4p5' in scenario and '2030' in scenario:
            continue

        output = []

        scenario_name = os.path.basename(scenario)[:-4]
        #print(scenario_name)
        path_out = os.path.join(folder_out, scenario_name + '.csv')

        for idx, country in countries.iterrows():

            if not collection_type == 'all':
                if not country['iso3'] == collection_type:
                    continue

            collect_country_regional_results(country['iso3'], scenario)

            scenario_name = os.path.basename(scenario)[:-4]
            #print('collecting national results for {}'.format(scenario_name))
            folder = os.path.join(DATA_PROCESSED, country['iso3'],
                'results', 'regional_aggregated', 'regions')

            if not os.path.exists(folder):
                #print('collect_national_results: folder does not exist: {}'.format(folder))
                return

            all_regional_results = os.listdir(folder)

            if len(all_regional_results) == 0:
                #print('len of all_regional_results = 0')
                return

            for filename in all_regional_results:

                path_in = os.path.join(folder, filename)
                # print(filename)
                if not os.path.exists(path_in):
                    continue
                try:
                    data = pd.read_csv(path_in)
                    data = data.to_dict('records')
                    output = output + data
                except:
                    print('failed on {})'.format(path_in))

        if len(output) == 0:
            #print('2. len of output = 0')
            return

        output = pd.DataFrame(output)

        output.to_csv(path_out, index=False)

    return


def collect_country_regional_results(iso3, scenario):
    """
    Collect regional results and write to national results folder.

    """
    output = []

    scenario_name = os.path.basename(scenario)[:-4]
    #print('collecting national results for {}'.format(scenario_name))
    folder = os.path.join(DATA_PROCESSED, iso3, 'results', 'regional_aggregated', 'regions')

    if not os.path.exists(folder):
        #print('collect_national_results: folder does not exist: {}'.format(folder))
        return

    all_regional_results = os.listdir(folder)

    if len(all_regional_results) == 0:
        #print('len of all_regional_results = 0')
        return

    for filename in all_regional_results:

        path_in = os.path.join(folder, filename)

        if not os.path.exists(path_in):
            continue
        try:
            data = pd.read_csv(path_in)
            data = data.to_dict('records')
            output = output + data
        except:
            print('failed on {}=)'.format(path_in))

    if len(output) == 0:
        #print('2. len of output = 0')
        return

    output = pd.DataFrame(output)

    folder_out = os.path.join(DATA_PROCESSED, iso3, 'results', 'regional_aggregated')
    if not os.path.exists(folder_out):
        print('folder out did not exist')
        os.mkdir(folder_out)
    path_out = os.path.join(folder_out, scenario_name + '.csv')
    output.to_csv(path_out, index=False)

    return


if __name__ == "__main__":

    args = sys.argv

    scenario = args[1]

    run_site_processing(scenario)
