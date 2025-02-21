"""
Collect validation results.

"""
import os
import configparser
import pandas as pd

from misc import get_countries, get_scenarios, get_regions, get_tropical_storm_scenarios

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__),'..', 'scripts', 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_PROCESSED = os.path.join(BASE_PATH, 'processed')


def collect(countries, scenarios):
    """
    Collect validation results.

    """
    # gid_level = 'GID_{}'.format(country['gid_region'])

    folder_in = os.path.join(DATA_PROCESSED, 'results', 'validation', 'country_data')
    # folder_out = os.path.join(DATA_PROCESSED, 'results', 'validation')

    # folder_in = os.path.join(BASE_PATH, '..','results','validation','country_data')

    if not os.path.exists(folder_in):
        os.makedirs(folder_in)

    for country in countries:
        
        #if not country['iso3'] in ['ARG']:
        #    continue

        # print("Working on {}".format(country['iso3']))

        output = []

        for scenario_path in scenarios:#[:1]:

            if '_perc_' in scenario_path:
                continue

            scenario = os.path.basename(scenario_path).replace('.tif','')

            # print('Working on {}'.format(scenario))

            country_folder = os.path.join(folder_in, country['iso3'], 'regional', scenario)

            min_depth = []
            mean_depth = []
            max_depth = []
            flooded_area_km2 = []

            if os.path.exists(country_folder):
                file_paths = os.listdir(country_folder)
                for filename in file_paths:

                    if not scenario in os.path.basename(filename).replace('.tif',''):
                        continue

                    path = os.path.join(country_folder, filename)
                    if not os.path.exists(path):
                        continue
                    else:
                        try:
                            data = pd.read_csv(path)
                        except:
                            continue
                        data = data.to_dict('records')
                        min_depth.append(data[0]['min_depth'])
                        mean_depth.append(data[0]['mean_depth'])
                        max_depth.append(data[0]['max_depth'])
                        flooded_area_km2.append(data[0]['flooded_area_km2'])

                if len(flooded_area_km2) > 0:
                    min_depth = min(min_depth)
                    mean_depth = sum(mean_depth) / len(mean_depth)
                    max_depth = max(max_depth)
                    flooded_area_km2 = sum(flooded_area_km2)
                else:
                    min_depth = "-"
                    mean_depth = "-"
                    median_depth = "-"
                    max_depth = "-"
                    flooded_area_km2 = "-"
            else:
                min_depth = "-"
                mean_depth = "-"
                median_depth = "-"
                max_depth = "-"
                flooded_area_km2 = "-"
            
            if 'river' in scenario:
                hazard = scenario.split('_')[0]
                climate_scenario = scenario.split('_')[1]
                model = scenario.split('_')[2]
                year = scenario.split('_')[3]
                return_period = scenario.split('_')[4]#[:-4]
                percentile = '-'

            if 'coast' in scenario:
                hazard = scenario.split('_')[0]
                climate_scenario = scenario.split('_')[1]
                model = scenario.split('_')[2]
                year = scenario.split('_')[3]
                return_period = scenario.split('_')[4]
                remaining_portion = scenario.split('_')[5]

                if not len(scenario.split('_')) > 6:
                    percentile = 0
                else:
                    percentile = scenario.split('_')[7]#[:-4]

            output.append({
                'iso3': country['iso3'],
                'hazard': hazard,
                'climate_scenario': climate_scenario,
                'model': model,
                'year': year,
                'return_period': return_period,
                'percentile': percentile,
                'min_depth': min_depth,
                'mean_depth': mean_depth,
                'max_depth': max_depth,
                'flooded_area_km2': flooded_area_km2,
            })

        output = pd.DataFrame(output)
        final_folder = os.path.join(folder_in, country['iso3'])
        if not os.path.exists(final_folder):
            continue 
        output.to_csv(os.path.join(final_folder, 'scenario_stats.csv'), index=False)

    return


def collect_all(countries):
    """
    Collect all results. 

    """
    # folder_in = os.path.join(BASE_PATH,'..','results','validation','country_data')
    folder_in = os.path.join(DATA_PROCESSED, 'results', 'validation', 'country_data')

    if not os.path.exists(folder_in):
        os.makedirs(folder_in)

    output = []

    for country in countries:
        
        #if not country['iso3'] == 'USA':
        #    continue

        path = os.path.join(folder_in, country['iso3'], 'scenario_stats.csv')

        if not os.path.exists(path):
            continue

        data = pd.read_csv(path)

        data = data.to_dict('records')

        output = output + data

    output = pd.DataFrame(output)
    folder_out = os.path.join(DATA_PROCESSED, 'results', 'validation')
    output.to_csv(os.path.join(folder_out,'..','scenario_stats.csv'),index=False)

    return


if __name__ == "__main__":

    countries = get_countries()
    scenarios = get_scenarios()
    #scenarios_tropical = get_tropical_storm_scenarios()

    collect(countries, scenarios)

    collect_all(countries)
