"""
Validation.

"""
import sys
import os
import configparser
import pandas as pd

from misc import get_countries

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__),'..', 'scripts', 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_PROCESSED = os.path.join(BASE_PATH, 'processed')


def collect_scenario_statistics():
    """
    Collect flooding statistics per country.

    """
    countries = get_countries()

    folder_out = os.path.join(BASE_PATH, '..', 'data', 'processed', 'results', 'validation')
    if not os.path.exists(folder_out):
        os.mkdir(folder_out)

    output = []

    for idx, country in countries.iterrows():

        if not country['iso3'] == 'USA':
            continue

        print('Working on {}'.format(country['iso3']))

        filename = '{}_scenario_stats.csv'.format(country['iso3'])
        path = os.path.join(DATA_PROCESSED, country['iso3'], 'hazards',
            'flooding', 'scenario_stats', filename) 
        
        if not os.path.exists(path):
            print('Path does not exist: {}'.format(path))
            continue

        #print('Working on {}'.format(country['iso3']))

        #try:
        data = pd.read_csv(path)
        data['iso3'] = country['iso3']
        data['country'] = country['country']
        data['continent'] = country['continent']
        data['income_group'] = country['income_group']
        data = data.to_dict('records')
        output = output + data
        #except:
        print('Failed on {}'.format(country['iso3']))
        
    output = pd.DataFrame(output)
    output.to_csv(os.path.join(folder_out, 'scenario_stats.csv'), index=False)

    return


if __name__ == "__main__":

    print('collecting scenario statistics')
    collect_scenario_statistics()
