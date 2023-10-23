"""
Collect results.

"""
import sys
import os
import configparser
import pandas as pd

from misc import get_countries, get_scenarios, get_regions

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__),'..', 'scripts', 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW = os.path.join(BASE_PATH, 'raw')
DATA_PROCESSED = os.path.join(BASE_PATH, 'processed')


def collect_regional_results(scenario):
    """
    Collect all results.

    """
    countries = get_countries()

    folder_out = os.path.join(DATA_PROCESSED, 'results', 'regional')

    if not os.path.exists(folder_out):
        os.mkdir(folder_out)

    output = []

    scenario_name = os.path.basename(scenario).replace('.tif','')#[:-4]
    path_out = os.path.join(folder_out, scenario_name + '_unique' + '.csv')

    for country in countries:

        # if not country['iso3'] == 'BGD':
        #     continue

        # print('Working on {}'.format(country['iso3']))

        regional_level = int(country['gid_region'])
        gid_level = 'GID_{}'.format(regional_level)
        regions = get_regions(country, regional_level)

        collect_country_regional_results(country, scenario, regions)

        folder_in = os.path.join(DATA_PROCESSED, country['iso3'],
            'results', 'regional_aggregated')

        if not os.path.exists(folder_in):
            # print('folder does not exist: {}'.format(folder_in))
            continue

        filename = "{}_unique.csv".format(scenario_name)
        path_in = os.path.join(folder_in, filename)

        if not os.path.exists(path_in):
            continue
        try:
            data = pd.read_csv(path_in)
            data = data.to_dict('records')
            output = output + data
        except:
            print('failed on {})'.format(path_in))

    if len(output) == 0:
        return

    output = pd.DataFrame(output)

    output.to_csv(path_out, index=False)

    return


def collect_country_regional_results(country, scenario, regions):
    """
    Collect regional results and write to national results folder.

    """
    output = []
    
    iso3 = country['iso3']
    regional_level = int(country['gid_region'])
    gid_level = 'GID_{}'.format(regional_level)
    
    filename = 'coastal_lookup.csv'
    folder = os.path.join(DATA_PROCESSED, iso3, 'coastal')
    path_coastal = os.path.join(folder, filename)
    if not os.path.exists(path_coastal):
        coastal_lut = []
    else:
        coastal_lut = pd.read_csv(path_coastal)
        coastal_lut = list(coastal_lut['gid_id'])

    scenario_name = os.path.basename(scenario).replace('.tif','')#[:-4]
    folder_in = os.path.join(DATA_PROCESSED, iso3, 'results', 
                            'regional_aggregated', 'regions')

    if not os.path.exists(folder_in):
        return

    for region in regions:

        if 'inuncoast' in scenario and region[gid_level] not in coastal_lut:
            print('Not coastal: {} in {}'.format(region[gid_level], scenario))
            continue

        filename = "{}_{}_unique.csv".format(region[gid_level], scenario)

        path_in = os.path.join(folder_in, filename)

        if not os.path.exists(path_in):
            continue
        try:
            data = pd.read_csv(path_in)
            data = data.to_dict('records')
            output = output + data
        except:
            print('failed on {})'.format(path_in))

    if len(output) == 0:
        return

    output = pd.DataFrame(output)

    folder_out = os.path.join(DATA_PROCESSED, iso3, 'results', 'regional_aggregated')
    if not os.path.exists(folder_out):
        print('folder out did not exist')
        os.mkdir(folder_out)

    path_out = os.path.join(folder_out, scenario_name + '_unique' + '.csv')
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

    scenario_name = os.path.basename(scenario).replace('.tif','')
    path_out = os.path.join(folder_out, scenario_name + '_unique' + '.csv')

    output = []

    folder_in = os.path.join(DATA_PROCESSED, 'results', 'regional')
    filename = os.path.join(scenario_name + '_unique' + '.csv')
    path_in = os.path.join(folder_in, filename)

    if not os.path.exists(path_in):
        return
    data = pd.read_csv(path_in, sep=',')
    countries = list(data['iso3'].unique())
    data = data.to_dict('records')

    for country in countries:

        # if not country == 'BGD':
        #     continue

        cell_count_baseline = 0
        cost_usd_baseline = 0

        for item in data:

            if not item['iso3'] == country:
                continue

            if item['cell_count_baseline'] > 0:
                cell_count_baseline += item['cell_count_baseline']

            if item['cost_usd_baseline'] > 0:
                cost_usd_baseline += item['cost_usd_baseline']

        output.append({
            'iso3': country,
            'cell_count_baseline': cell_count_baseline,
            'cost_usd_baseline': cost_usd_baseline,
            })

    if len(output) == 0:
        return

    output = pd.DataFrame(output)

    output.to_csv(path_out, index=False)

    return


if __name__ == "__main__":

    args = sys.argv

    print('collecting regional results')
    collect_regional_results(args[1])

    print('collecting final results')
    collect_final_results(args[1])

