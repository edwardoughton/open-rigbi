"""
Estimate results, inc. economic impacts.

Written by Ed Oughton.

February 2022.

"""
import os
import configparser
import pandas as pd
from tqdm import tqdm
import numpy as np

from misc import params, technologies, get_countries, get_regions, get_scenarios


CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW = os.path.join(BASE_PATH, 'raw')
DATA_PROCESSED = os.path.join(BASE_PATH, 'processed')
RESULTS = os.path.join(BASE_PATH, '..', 'results')


def econ_interim_impacts(country, technologies, scenarios):
    """
    Estimate economic impacts.

    Aqueduct flood scenarios as structured as follows:

    floodtype_climatescenario_subsidence_year_returnperiod_projection

    """
    iso3 = country['iso3']

    filename = 'econ_interim_{}.csv'.format(iso3)
    folder_out = os.path.join(RESULTS)
    path_output = os.path.join(folder_out, filename)

    if os.path.exists(path_output):
        return

    output = []

    for scenario in tqdm(scenarios):
        for technology in technologies:

            scenario = os.path.basename(scenario)
            filename = 'sites_{}_{}.csv'.format(technology, scenario)
            folder = os.path.join(DATA_PROCESSED, country['iso3'], 'failed_sites')
            path = os.path.join(folder, filename)

            data = pd.read_csv(path)

            data = data.to_dict('records')#[:10000]

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

            affected_sites = 0
            cost = 0
            for item in data:
                if item['scenario'] == scenario:
                    if item['fragility'] > 0:
                        affected_sites += 1
                        cost += (100000 * item['fragility'])

            output.append({
                'floodtype': floodtype,
                'climatescenario': climatescenario,
                'subsidence': subsidence,
                'year': year,
                'returnperiod': returnperiod,
                'projection': projection,
                'technology': technology,
                'affected_sites': affected_sites,
                'cost': cost,
                'scenario': scenario,
            })

    output = pd.DataFrame(output)

    if not os.path.exists(folder_out):
        os.mkdir(folder_out)

    output.to_csv(path_output, index=False)

    return


def econ_final_impacts(country):
    """
    Compare economic impacts against historical.

    Aqueduct flood scenarios as structured as follows:

    floodtype_climatescenario_subsidence_year_returnperiod_projection

    """
    iso3 = country['iso3']

    filename = 'econ_interim_{}.csv'.format(iso3)
    folder_in = os.path.join(RESULTS)
    path_in = os.path.join(folder_in, filename)

    if not os.path.exists(path_in):
        return

    data = pd.read_csv(path_in)
    data = process_edit_return_periods(data)
    data = add_model_average(data, 'cost')

    ### Add hist baseline to inuncoast
    inuncoast = data.loc[data['floodtype'] == 'inuncoast']
    historical = inuncoast.loc[inuncoast['climatescenario'] == 'historical']
    scenarios = inuncoast.loc[inuncoast['climatescenario'] != 'historical']
    historical = historical[['returnperiod', 'technology', 'affected_sites', 'cost']].reset_index()
    historical = historical.rename({'affected_sites': 'hist_affected_sites', 'cost': 'hist_cost'}, axis=1)
    historical.drop('index', axis=1, inplace=True)
    inuncoast = pd.merge(scenarios, historical,  how='left', on=['returnperiod', 'technology'])

    ### Add hist baseline to inunriver
    inunriver = data.loc[data['floodtype'] == 'inunriver']
    historical = inunriver.loc[inunriver['climatescenario'] == 'historical']
    scenarios = inunriver.loc[inunriver['climatescenario'] != 'historical']
    historical = historical[['returnperiod', 'technology', 'affected_sites', 'cost']].reset_index()
    historical = historical.rename({'affected_sites': 'hist_affected_sites', 'cost': 'hist_cost'}, axis=1)
    historical.drop('index', axis=1, inplace=True)
    inunriver = pd.merge(scenarios, historical,  how='left', on=['returnperiod', 'technology'])

    output = pd.concat([inuncoast, inunriver])

    output['sites_difference'] = output['affected_sites'] - output['hist_affected_sites']
    output['cost_difference'] = output['cost'] - output['hist_cost']

    filename = 'econ_final_{}.csv'.format(iso3)
    folder_out = os.path.join(RESULTS)
    path_output = os.path.join(folder_out, filename)
    output.to_csv(path_output, index=False)

    return


def process_edit_return_periods(data):
    """
    Correct differences in the return period text.

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

    output = pd.DataFrame(output)

    return output


def add_model_average(data, metric):
    """
    Take the model average for inunriver.

    """
    inuncoast = data.loc[data['floodtype'] == 'inuncoast']
    inunriver = data.loc[data['floodtype'] == 'inunriver']

    historical = inunriver.loc[data['climatescenario'] == 'historical']
    inunriver = inunriver.loc[data['climatescenario'] != 'historical']

    scenarios = inunriver['climatescenario'].unique()
    years = inunriver['year'].unique()
    returnperiods = inunriver['returnperiod'].unique()
    technologies = inunriver['technology'].unique()
    models = inunriver['subsidence'].unique()

    output = []

    for scenario in scenarios:
        subset_scenarios = inunriver.loc[inunriver['climatescenario'] == scenario]
        for year in years:
            subset_year = subset_scenarios.loc[subset_scenarios['year'] == year]
            for returnperiod in returnperiods:
                subset_rp = subset_year.loc[subset_year['returnperiod'] == returnperiod]
                if len(subset_rp) == 0:
                    continue
                for technology in technologies:
                    subset_tech = subset_rp.loc[subset_rp['technology'] == technology]
                    if len(subset_tech) == 0:
                        continue
                    # affected_sites = []
                    mean_list = []
                    for model in models:
                        subset_model = subset_tech.loc[subset_tech['subsidence'] == model]
                        if len(subset_model) == 0:
                            continue
                        # affected_sites.append(subset_model['affected_sites'].values[0])
                        mean_list.append(subset_model[metric].values[0])

                    output.append({
                        'floodtype': 'inunriver',
                        'climatescenario': scenario,
                        'subsidence': 'model_mean',
                        'year': year,
                        'returnperiod': returnperiod,
                        'projection': 'nunriver',
                        'technology': technology,
                        # 'affected_sites': int(round(np.mean(affected_sites))),
                        metric: int(round(np.mean(mean_list))),
                        'scenario': 'model_mean',
                    })

    output = pd.DataFrame(output)
    output = pd.concat([inuncoast, historical, inunriver, output])

    output = output.drop_duplicates()

    return output


def coverage_interim_impacts(country, regions, technologies, scenarios):
    """
    Estimate coverage.

    Aqueduct flood scenarios as structured as follows:

    floodtype_climatescenario_subsidence_year_returnperiod_projection

    """
    iso3 = country['iso3']

    filename = 'coverage_interim_{}.csv'.format(iso3)
    folder_out = os.path.join(RESULTS)
    path_output = os.path.join(folder_out, filename)

    # if os.path.exists(path_output):
    #     return

    output = []

    for scenario in tqdm(scenarios):

        scenario = os.path.basename(scenario)

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

        for technology in tqdm(technologies):

            population_covered = 0

            for idx, region in regions.iterrows():

                regional_level = country['gid_region']
                gid_level = 'GID_{}'.format(regional_level)
                gid_id = region[gid_level]

                filename = 'covered_{}_{}_{}.csv'.format(gid_id, technology, scenario)
                folder_out = os.path.join(DATA_PROCESSED, iso3, 'regional_data', gid_id, technology)
                path_in = os.path.join(folder_out, filename)

                if not os.path.exists(path_in):
                    continue
                data = pd.read_csv(path_in)

                pop = data['population'].sum()
                if pop > 0:
                    population_covered += pop

            output.append({
                'floodtype': floodtype,
                'climatescenario': climatescenario,
                'subsidence': subsidence,
                'year': year,
                'returnperiod': returnperiod,
                'projection': projection,
                'covered_population': population_covered,
                'technology': technology,
                'scenario': scenario,
            })

    output = pd.DataFrame(output)

    if not os.path.exists(folder_out):
        os.mkdir(folder_out)

    output.to_csv(path_output, index=False)

    return


def coverage_final_impacts(country):
    """
    Compare coverage impacts against historical.

    Aqueduct flood scenarios as structured as follows:

    floodtype_climatescenario_subsidence_year_returnperiod_projection

    """
    iso3 = country['iso3']

    filename = 'coverage_interim_{}.csv'.format(iso3)
    folder_in = os.path.join(RESULTS)
    path_in = os.path.join(folder_in, filename)

    if not os.path.exists(path_in):
        return

    data = pd.read_csv(path_in)
    data = process_edit_return_periods(data)
    data = add_model_average(data, 'covered_population')

    ### Add hist baseline to inuncoast
    inuncoast = data.loc[data['floodtype'] == 'inuncoast']
    historical = inuncoast.loc[inuncoast['climatescenario'] == 'historical']
    scenarios = inuncoast.loc[inuncoast['climatescenario'] != 'historical']
    historical = historical[['returnperiod', 'technology', 'covered_population']].reset_index()
    historical = historical.rename({'covered_population': 'hist_covered_population'}, axis=1)
    historical.drop('index', axis=1, inplace=True)
    inuncoast = pd.merge(scenarios, historical,  how='left', on=['returnperiod', 'technology'])

    ### Add hist baseline to inunriver
    inunriver = data.loc[data['floodtype'] == 'inunriver']
    historical = inunriver.loc[inunriver['climatescenario'] == 'historical']
    scenarios = inunriver.loc[inunriver['climatescenario'] != 'historical']
    historical = historical[['returnperiod', 'technology', 'covered_population']].reset_index()
    historical = historical.rename({'covered_population': 'hist_covered_population'}, axis=1)
    historical.drop('index', axis=1, inplace=True)
    inunriver = pd.merge(scenarios, historical,  how='left', on=['returnperiod', 'technology'])

    output = pd.concat([inuncoast, inunriver]).reset_index()
    output['covered_difference'] = output['covered_population'] - output['hist_covered_population']
    output.drop('index', axis=1, inplace=True)

    filename = 'coverage_final_{}.csv'.format(iso3)
    folder_out = os.path.join(RESULTS)
    path_output = os.path.join(folder_out, filename)
    output.to_csv(path_output, index=False)

    return


def coverage_estimation_using_failures(country, regions, technologies, scenarios):
    """
    Estimate coverage.

    Aqueduct flood scenarios as structured as follows:

    floodtype_climatescenario_subsidence_year_returnperiod_projection

    """
    iso3 = country['iso3']

    filename = 'pop_affected_by_failures_{}.csv'.format(iso3)
    folder_out = os.path.join(RESULTS)
    path_output = os.path.join(folder_out, filename)

    # if not os.path.exists(path_output):
    #     return

    output = []

    for scenario in scenarios: #tqdm(scenarios):

        scenario = os.path.basename(scenario)

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

        for technology in technologies:

            population_covered = 0

            filename = 'pop_affected_by_failures_{}_{}.csv'.format(technology, scenario)
            folder_in = os.path.join(DATA_PROCESSED, iso3, 'failed_sites', 'coverage')
            path_in = os.path.join(folder_in, filename)

            if not os.path.exists(path_in):
                continue
            data = pd.read_csv(path_in)

            pop = data['pop_covered'].sum()
            if pop > 0:
                population_covered += pop

            output.append({
                'floodtype': floodtype,
                'climatescenario': climatescenario,
                'subsidence': subsidence,
                'year': year,
                'returnperiod': returnperiod,
                'projection': projection,
                'covered_population': population_covered,
                'technology': technology,
                'scenario': scenario,
            })

    output = pd.DataFrame(output)

    if not os.path.exists(folder_out):
        os.mkdir(folder_out)

    output.to_csv(path_output, index=False)

    return



def load_site_results(country):
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

    output.to_csv(os.path.join(RESULTS, 'site_data.csv'), index=False)

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


if __name__ == "__main__":

    countries = get_countries()

    for idx, country in countries.iterrows():

        if not country['iso3'] == 'GHA':
            continue

        regions = get_regions(country)
        scenarios = get_scenarios(country)#[:1]

        econ_interim_impacts(country, technologies, scenarios)

        econ_final_impacts(country)

        coverage_interim_impacts(country, regions, technologies, scenarios)

        coverage_final_impacts(country)

        coverage_estimation_using_failures(country, regions, technologies, scenarios)

        load_site_results(country)
