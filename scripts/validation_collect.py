"""
Collect validation results.

"""
import sys
import os
import configparser
import pandas as pd

from misc import get_countries, get_scenarios

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__),'..', 'scripts', 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_PROCESSED = os.path.join(BASE_PATH, 'processed')


def collect(countries, scenarios):
    """
    Collect validation results.

    """
    output = []

    folder_in = os.path.join(DATA_PROCESSED, 'results', 'validation', 'country_data')
    folder_out = os.path.join(DATA_PROCESSED, 'results', 'validation')

    for idx, country in countries.iterrows():
        
        print("Working on {}".format(country['iso3']))        

        for scenario_path in scenarios:
            
            scenario = os.path.basename(scenario_path)#[:-4]
            
            path = os.path.join(folder_in, country['iso3'], scenario[:-4] + '.csv')
                        
            if not os.path.exists(path):
                if 'river' in scenario:
                    hazard = scenario.split('_')[0]
                    climate_scenario = scenario.split('_')[1]
                    model = scenario.split('_')[2]
                    year = scenario.split('_')[3]
                    return_period = scenario.split('_')[4][:-4]
                    percentile = '-'

                if 'coast' in scenario:
                    hazard = scenario.split('_')[0]
                    climate_scenario = scenario.split('_')[1]
                    model = scenario.split('_')[2]
                    year = scenario.split('_')[3]
                    return_period = scenario.split('_')[4]
                    remaining_portion = scenario.split('_')[5]
                    if remaining_portion == '0.tif':
                        percentile = 0
                    else:
                        percentile = scenario.split('_')[7][:-4]

                output.append({
                    'iso3': country['iso3'],
                    'hazard': hazard,
                    'climate_scenario': climate_scenario,
                    'model': model,
                    'year': year,
                    'return_period': return_period,
                    'percentile': percentile,
                    'min_depth': "-",
                    'mean_depth': "-",
                    'median_depth': "-",
                    'max_depth': "-",
                    'flooded_area_km2': "-",
                })

            else:
                try: 
                    data = pd.read_csv(path)
                except:
                    continue
                data['iso3'] = country['iso3']                 
                data = data.to_dict('records')
                output = output + data

    output = pd.DataFrame(output)
    output.to_csv(os.path.join(folder_out, 'scenario_stats.csv'), index=False)

    return


if __name__ == "__main__":

    countries = get_countries()
    scenarios = get_scenarios()

    collect(countries, scenarios)
