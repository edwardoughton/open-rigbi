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


def load_results(country):
    """
    Load results.

    """
    iso3 = country['iso3']

    filename = 'final_{}.csv'.format(iso3)
    folder_in = os.path.join(RESULTS)
    path_in = os.path.join(folder_in, filename)

    data = pd.read_csv(path_in)

    # data = data[data['projection'] != '0_perc_05']
    # data = data[data['projection'] != '0_perc_50']

    # data = data[data['subsidence'] != '00000NorESM1-M']
    # data = data[data['subsidence'] != '0000HadGEM2-ES']
    # data = data[data['subsidence'] != '00IPSL-CM5A-LR']
    # data = data[data['subsidence'] != 'MIROC-ESM-CHEM']
    # data = data[data['subsidence'] != 'wtsub']

    data = process_edit_return_periods(data)

    # data = edit_year(data)

    data = pd.DataFrame(data)

    data = data.groupby([
        # 'floodtype',
        'climatescenario',
        # 'subsidence',
        'year',
        'returnperiod',
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
            'cost': item['cost'],
        })

    output = pd.DataFrame(output)

    output.to_csv(os.path.join(VIS, 'test_data.csv'), index=False)

    return output


def process_edit_return_periods(data):
    """
    Process data.

    """
    output = []

    for idx, item in data.iterrows():

        rn_name = item['returnperiod']

        if rn_name == 'rp01000' or rn_name == 'rp1000':
            item['returnperiod'] = '1000-year'
        elif rn_name == 'rp00500' or rn_name == 'rp0500':
            item['returnperiod'] = '500-year'
        elif rn_name == 'rp00250' or rn_name == 'rp0250':
            item['returnperiod'] = '250-year'
        elif rn_name == 'rp00100' or rn_name == 'rp0100':
            item['returnperiod'] = '100-year'
        else:
            print('Return period not recognized')

        output.append(item)

    return output


def edit_year(data):
    """

    """
    output = []

    for item in data:

        # if item['year'] in ('2030', '2050', '2080'):
        #     output.append(item)
        if item['year'] == 'hist' or item['year'] == '1980':
            item['year'] = 'historical'

        output.append(item)

    return output


def generate_curves(results):
    """
    Generate curves.

    """
    results = pd.DataFrame(results)

    results['year'] = pd.Categorical(
        results['year'],
        categories=['historical', '2030', '2050', '2080'],
        ordered=True
    )

    fig, axes = plt.subplots(2, 2, figsize=(10,10))

    my_axes = [
        (0,0,'100-year'),
        (0,1,'250-year'),
        (1,0,'500-year'),
        (1,1,'1000-year'),
    ]

    for item in my_axes:

        col = item[0]
        row = item[1]

        subset = results.loc[
            results['returnperiod'] == item[2]
            ]

        sns.lineplot(x=subset['year'], y=subset['cost'],
                    hue=subset['climatescenario'], #style=subset['climatescenario'],
                    # order=['historical', '2030', '2050', '2080'],
                    # kind='point',
                    data=subset, ax= axes[col][row]
                    )

    # sns.catplot(x=results['year'], y=results['cost'],
    #             hue=results['climatescenario'], #style=results['climatescenario'],
    #             # order=['historical', '2030', '2050', '2080'],
    #             row=results['returnperiod'],
    #             kind='point',
    #             data=results, #ax= axes[col][row]
    #             )

    fig.tight_layout()

    main_title = 'Results.png'
    plt.suptitle(main_title, fontsize=16, y=1.03)

    plt.savefig(os.path.join(VIS, 'test_plot.png'),
        pad_inches=0.4,
        bbox_inches='tight'
    )

    plt.close()



if __name__ == '__main__':

    filename = "countries.csv"
    path = os.path.join(DATA_RAW, filename)
    countries = pd.read_csv(path, encoding='latin-1')

    for idx, country in countries.iterrows():

        if not country['iso3'] == 'GHA':
            continue

        iso3 = country['iso3']

        print('Working on {}'.format(iso3))

        results = load_results(country)
        results = pd.DataFrame(results)
        results.to_csv(os.path.join(VIS, 'test_results.csv'), index=False)

        # generate_curves(results)

    print('Complete')
