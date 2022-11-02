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

from misc import (process_country_shapes, process_regions, params, technologies,
    get_countries, get_regions, get_scenarios)

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
    if not os.path.exists(folder_out):
        os.mkdir(folder_out)

    # for scenario in scenarios:

        # if not 'rcp4p5' in scenario and '2030' in scenario:
        #     continue

    output = []

    scenario_name = os.path.basename(scenario)[:-4]

    path_out = os.path.join(folder_out, scenario_name + '.csv')

    for idx, country in countries.iterrows():

        # if not collection_type == 'all':
        #     if not country['iso3'] == collection_type:
        #         continue

        collect_country_regional_results(country['iso3'], scenario)

        scenario_name = os.path.basename(scenario)[:-4]
        print('collecting national results for {}'.format(country['iso3']))
        folder = os.path.join(DATA_PROCESSED, country['iso3'],
            'results', 'regional_aggregated', 'regions')

        if not os.path.exists(folder):
            print('collect_national_results: folder does not exist: {}'.format(folder))
            continue

        all_regional_results = os.listdir(folder)

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

    folder_out = os.path.join(DATA_PROCESSED, iso3, 'results', 'regional_aggregated')
    if not os.path.exists(folder_out):
        print('folder out did not exist')
        os.mkdir(folder_out)

    path_out = os.path.join(folder_out, scenario_name + '.csv')
    output.to_csv(path_out, index=False)

    return


if __name__ == "__main__":

    args = sys.argv

    collect_regional_results(args[1])

    # if len(args[1]) > 0:
    #     # collect_final_results(args[2])
    #     collect_regional_results(args[1])
    # else:
    #     # collect_final_results('all')
    #     collect_regional_results('all')
