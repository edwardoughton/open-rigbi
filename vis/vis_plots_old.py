"""


"""
import os
import configparser
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), '..', 'scripts', 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW = os.path.join(BASE_PATH, 'raw')
DATA_PROCESSED = os.path.join(BASE_PATH, 'processed')
RESULTS = os.path.join(BASE_PATH, '..', 'results')
VIS = os.path.join(BASE_PATH, '..', 'vis', 'figures')
REPORTS = os.path.join(BASE_PATH, '..', 'reports', 'images')


def load_coverage_results(country):
    """
    Load results.

    """
    iso3 = country['iso3']

    filename = 'baseline_coverage.csv'
    folder_in = os.path.join(DATA_PROCESSED, iso3)
    path_in = os.path.join(folder_in, filename)
    baseline = pd.read_csv(path_in)
    baseline = baseline[['technology', 'covered_pop', 'uncovered_pop']]
    baseline = baseline.groupby(['technology'], as_index=True).sum().reset_index()

    filename = 'coverage_final_{}.csv'.format(iso3)
    folder_in = os.path.join(RESULTS)
    path_in = os.path.join(folder_in, filename)
    data = pd.read_csv(path_in)
    data = data.merge(baseline, left_on='technology', right_on='technology')
    data.reset_index(drop=True, inplace=True)

    data.to_csv(os.path.join(VIS, 'test.csv'))

    # data = data[data['projection'] != '0_perc_05']
    # data = data[data['projection'] != '0_perc_50']

    # data = data[data['subsidence'] != '00000NorESM1-M']
    # data = data[data['subsidence'] != '0000HadGEM2-ES']
    # data = data[data['subsidence'] != '00IPSL-CM5A-LR']
    # data = data[data['subsidence'] != 'MIROC-ESM-CHEM']
    # data = data[data['subsidence'] != 'wtsub']

    # data = process_edit_return_periods(data)

    # data = edit_year(data)

    data = pd.DataFrame(data)

    data['coverage_change'] = data['covered_population'] - data['covered_pop']

    data = data.groupby([
        # 'floodtype',
        'climatescenario',
        # 'subsidence',
        'year',
        'returnperiod',
        'technology',
        # 'projection'
        ], as_index=True).sum().reset_index()

    output = []

    for idx, item in data.iterrows():

        # if item['climatescenario'] == 'historical':
        #     cost = item['cost'] / 2
        # elif item['climatescenario'] == 'rcp4p5':
        #     cost = item['cost'] * 1.2
        # elif item['climatescenario'] == 'rcp8p5':
        #     cost = item['cost'] * 1.6

        output.append({
            'climatescenario': item['climatescenario'],
            'year': item['year'],
            'returnperiod': item['returnperiod'],
            'technology': item['technology'],
            # 'coverage_baseline': item['covered_pop'],
            # 'covered_population': item['covered_population'],
            'coverage_change': item['coverage_change'],
            # 'uncovered_population': item['uncovered_population'],
        })

    output = pd.DataFrame(output)

    output.to_csv(os.path.join(VIS, 'coverage_data.csv'), index=False)

    return output


if __name__ == '__main__':

    filename = "countries.csv"
    path = os.path.join(DATA_RAW, filename)
    countries = pd.read_csv(path, encoding='latin-1')

    for idx, country in countries.iterrows():

        if not country['iso3'] == 'GHA':
            continue

        iso3 = country['iso3']

        print('Working on {}'.format(iso3))

        # results = load_site_results(country)
        # results = pd.DataFrame(results)
        # results.to_csv(os.path.join(VIS, 'site_results.csv'), index=False)

        results = load_coverage_results(country)
        results = pd.DataFrame(results)
        results.to_csv(os.path.join(VIS, 'coverage_results.csv'), index=False)

        # generate_curves(results)

    print('Complete')
