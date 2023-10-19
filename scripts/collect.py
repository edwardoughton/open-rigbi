"""
Collect results.

"""
import sys
import os
import configparser
import pandas as pd

from misc import get_countries, get_scenarios

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

        if not country['iso3'] == 'ARG':
            continue

        # print('Working on {}'.format(country['iso3']))

        collect_country_regional_results(country['iso3'], scenario)

        folder_in = os.path.join(DATA_PROCESSED, country['iso3'],
            'results', 'regional_aggregated', 'regions')

        if not os.path.exists(folder_in):
            # print('folder does not exist: {}'.format(folder_in))
            continue

        all_regional_results = os.listdir(folder_in)#[:1]
        if len(all_regional_results) == 0:
            print('len of all_regional_results = 0')
            continue

        for filename in all_regional_results:

            filename = filename.replace('.csv','')

            if not scenario_name in filename:
                continue

            if not 'unique' in filename:
                continue

            # if not 'STORM' in filename:
            #     continue

            path_in = os.path.join(folder_in, filename + '.csv')
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
    # print('writing: {}'.format(path_out))
    output.to_csv(path_out, index=False)

    return


def collect_country_regional_results(iso3, scenario):
    """
    Collect regional results and write to national results folder.

    """
    output = []

    scenario_name = os.path.basename(scenario).replace('.tif','')#[:-4]
    folder_in = os.path.join(DATA_PROCESSED, iso3, 'results', 
                            'regional_aggregated', 'regions')

    if not os.path.exists(folder_in):
        return

    all_regional_results = os.listdir(folder_in)#[:1]

    if len(all_regional_results) == 0:
        return

    for filename in all_regional_results:

        if not scenario_name in filename:
            continue

        if not 'unique' in filename:
            continue

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
    iso3 = list(data['iso3'].unique())
    data = data.to_dict('records')

    for country in country:

        if not country == 'ARG':
            continue

        cell_count_baseline = 0
        cost_usd_baseline = 0

        for item in data:

            if not item['iso3'] == iso3:
                continue

            if item['cost_usd_baseline'] > 0:
                cell_count_baseline += 1
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

