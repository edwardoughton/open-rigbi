"""
Collect results.

"""
import sys
import os
import configparser
import pandas as pd
# import geopandas as gpd
# import pyproj
# from shapely.ops import transform
# from shapely.geometry import shape, Point, mapping, LineString, MultiPolygon
# from tqdm import tqdm
# import rasterio
# import random

from misc import get_countries

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__),'..', 'scripts', 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW = os.path.join(BASE_PATH, 'raw')
DATA_PROCESSED = os.path.join(BASE_PATH, 'processed')


def collect_regional_results(scenario):
    """
    Collect all results.

    """
    # scenarios = get_scenarios()[::-1]
    countries = get_countries()

    folder_out = os.path.join(DATA_PROCESSED, 'results', 'regional')
    #if not os.path.exists(folder_out):
    #    os.mkdir(folder_out)

    # for scenario in scenarios:

        # if not 'rcp4p5' in scenario and '2030' in scenario:
        #     continue

    output = []

    scenario_name = os.path.basename(scenario)#[:-4]
    print(scenario)
    path_out = os.path.join(folder_out, scenario_name + '.csv')

    for idx, country in countries.iterrows():
        print(country['iso3'])
        # if not collection_type == 'all':
        #     if not country['iso3'] == collection_type:
        #         continue

        collect_country_regional_results(country['iso3'], scenario)

        scenario_name = os.path.basename(scenario)#[:-4]
        print('collecting national results for {}'.format(country['iso3']))
        folder = os.path.join(DATA_PROCESSED, country['iso3'],
            'results', 'regional_aggregated', 'regions')

        if not os.path.exists(folder):
            print('collect_national_results: folder does not exist: {}'.format(folder))
            continue

        all_regional_results = os.listdir(folder)#[:1]
        print(all_regional_results)
        if len(all_regional_results) == 0:
            print('len of all_regional_results = 0')
            continue

        for filename in all_regional_results:

            path_in = os.path.join(folder, filename)
            #print(filename)
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
    print('writing: {}'.format(path_out))
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

    all_regional_results = os.listdir(folder)#[:1]

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

    folder_out = os.path.join(DATA_PROCESSED, iso3, 'results', 'regional_aggregated')
    if not os.path.exists(folder_out):
        print('folder out did not exist')
        os.mkdir(folder_out)

    path_out = os.path.join(folder_out, scenario_name + '.csv')
    output.to_csv(path_out, index=False)

    return



def collect_final_results(scenario):
    """
    Collect all results.

    """
    countries = get_countries()

    folder_out = os.path.join(DATA_PROCESSED, 'results')
    if not os.path.exists(folder_out):
        os.mkdir(folder_out)

    output = []

    scenario_name = os.path.basename(scenario)#[:-4]

    path_out = os.path.join(folder_out, scenario_name + '.csv')

    for idx, country in countries.iterrows():

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
                    'cell_count_low': 0,
                    'cell_count_baseline': 0,
                    'cell_count_high': 0,
                    'cost_usd_low': 0,
                    'cost_usd_baseline': 0,
                    'cost_usd_high': 0,
                })
            continue

        data = pd.read_csv(path, sep=',')

        if len(data) == 0:
            continue

        radios = list(data['radio'].unique())
        # networks = list(data['net'].unique())

        for radio in radios:

            cell_count_low = 0
            cell_count_baseline = 0
            cell_count_high = 0
            cost_usd_low = 0
            cost_usd_baseline = 0
            cost_usd_high = 0

            for idx, item in data.iterrows():

                if not item['radio'] == radio:
                    continue

                if not item['failure'] == 1:
                    continue

                cell_count_low += 1
                cell_count_baseline += 1
                cell_count_high += 1
                cost_usd_low += item['cost_usd_low']
                cost_usd_baseline += item['cost_usd_baseline']
                cost_usd_high += item['cost_usd_high']

            output.append({
                'iso3': country['iso3'],
                'iso2': country['iso2'],
                'country': country['country'],
                'continent': country['continent'],
                'radio': radio,
                #'network': network,
                'cell_count': cell_count,
                'cost_usd': cost_usd,
                 'cell_count_low': 0,
                    'cell_count_baseline': 0,
                    'cell_count_high': 0,
                    'cost_usd_low': 0,
                    'cost_usd_baseline': 0,
                    'cost_usd_high': 0,
                })

    if len(output) == 0:
        # print('output len = 0')
        return

    output = pd.DataFrame(output)

    output.to_csv(path_out, index=False)

    return


def collect_national_results(iso3, scenario):
    """
    Collect regional results and write to national results folder.

    """
    output = []

    scenario_name = os.path.basename(scenario)#[:-4]
    #print('collecting national results for {}'.format(scenario_name))
    folder = os.path.join(DATA_PROCESSED, iso3, 'results', 'regional_data', scenario_name)

    if not os.path.exists(folder):
        #print('collect_national_results: folder does not exist: {}'.format(folder))
        return

    all_regional_results = os.listdir(folder)#[:1]

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


if __name__ == "__main__":

    args = sys.argv

    print('collecting regional results')
    collect_regional_results(args[1])

    print('collecting final results')
    collect_final_results(args[1])
