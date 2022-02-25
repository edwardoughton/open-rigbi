"""
Estimate economic impacts.

Written by Ed Oughton.

February 2022.

"""
import os
import configparser
import pandas as pd
from tqdm import tqdm

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW = os.path.join(BASE_PATH, 'raw')
DATA_PROCESSED = os.path.join(BASE_PATH, 'processed')
RESULTS = os.path.join(BASE_PATH, '..', 'results')


def get_scenarios(scenarios):
    """

    """
    output = []

    return_periods = [
        'rp0100',
        'rp0250',
        'rp0500',
        'rp1000',
        'rp00100',
        'rp00250',
        'rp00500',
        'rp01000'
    ]

    # for scenario in scenarios:

        # if any(x in scenario for x in return_periods): #specify return periods

        #     if 'inunriver' in scenario: #use only no subsidence

        #         if 'MIROC-ESM-CHEM' in scenario:

        # output.append(scenario)

    for scenario in scenarios:

        if any(x in scenario for x in return_periods): #specify return periods

            if 'inuncoast' and 'wtsub' in scenario: #use only no subsidence
                if '0_perc_50.tif' in scenario:
                    output.append(scenario)
            elif 'inunriver' and 'MIROC-ESM-CHEM' in scenario:
                output.append(scenario)
            else:
                continue

    return output


def estimate_econ_impacts(country):
    """
    Estimate economic impacts.

    Aqueduct flood scenarios as structured as follows:

    floodtype_climatescenario_subsidence_year_returnperiod_projection

    """
    iso3 = country['iso3']

    filename = 'sites_{}.csv'.format(iso3)
    folder = os.path.join(RESULTS)
    path = os.path.join(folder, filename)

    if not os.path.exists(path):
        return

    data = pd.read_csv(path)
    scenarios = data['scenario'].unique()#[:1]
    scenarios = get_scenarios(scenarios)

    data = data.to_dict('records')#[:10000]

    output = []

    for scenario in tqdm(scenarios):

        # if not 'historical' in scenario:
        #     continue

        ### floodtype_climatescenario_subsidence_year_returnperiod_projection
        floodtype = scenario.split('_')[0]
        climatescenario = scenario.split('_')[1]
        subsidence = scenario.split('_')[2]
        year = scenario.split('_')[3]
        returnperiod = scenario.split('_')[4].strip('.tif')
        projection = scenario.split('_')[5:] #not all same length

        if floodtype == 'inuncoast': #deal with differences between climate scenarios
            projection = '_'.join(projection)
        elif floodtype == 'inunriver':
            projection = 'inunriver'
        else:
            print('Did not recognize floodtype')
        projection = projection.strip('.tif')

        # failures = 0
        cost = 0
        for item in data:

            if item['scenario'] == scenario:
                # if item['failure'] == 1:
                #     print(item)
                #     failures += 1
                if item['fragility'] > 0:
                    # print(item)
                    cost += (100000 * item['fragility'])
                # else:
                #     cost += 0

        output.append({
            'floodtype': floodtype,
            'climatescenario': climatescenario,
            'subsidence': subsidence,
            'year': year,
            'returnperiod': returnperiod,
            'projection': projection,
            # 'failures': failures,
            # 'cost': (failures * 20000),
            'cost': cost,
            'scenario': scenario,
        })

    output = pd.DataFrame(output)

    filename = 'final_{}.csv'.format(iso3)
    folder_out = os.path.join(RESULTS)
    path_output = os.path.join(folder_out, filename)

    if not os.path.exists(folder_out):
        os.mkdir(folder_out)

    output.to_csv(path_output, index=False)

    return


if __name__ == "__main__":

    filename = "countries.csv"
    path = os.path.join(DATA_RAW, filename)
    countries = pd.read_csv(path, encoding='latin-1')

    for idx, country in countries.iterrows():

        if not country['iso3'] == 'GHA':
            continue

        iso3 = country['iso3']

        print('Working on {}'.format(iso3))

        # scenarios = get_scenarios(country)
        estimate_econ_impacts(country)
