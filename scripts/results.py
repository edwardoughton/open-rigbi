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
import geopandas as gpd
import rasterio
import random

from misc import params, technologies, get_countries, get_regions, get_scenarios
from flood_hazards import process_flooding_layers

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW = os.path.join(BASE_PATH, 'raw')
DATA_PROCESSED = os.path.join(BASE_PATH, 'processed')
RESULTS = os.path.join(BASE_PATH, '..', 'results')


def query_hazard_layers(country, regions, scenarios):
    """
    Query each hazard layer and estimate fragility.

    """
    iso3 = country['iso3']
    name = country['country']
    regional_level = country['lowest']
    gid_level = 'GID_{}'.format(1) #regional_level

    filename = 'fragility_curve.csv'
    path_fragility = os.path.join(DATA_RAW, filename)
    f_curve = pd.read_csv(path_fragility)
    f_curve = f_curve.to_dict('records')

    regions = get_regions(country, 1)#[:50]
    # regions = regions[regions['GID_1'] == 'AFG.14_1']

    for scenario in tqdm(scenarios):

        # if not scenario == 'data\processed\MWI\hazards\inunriver_rcp8p5_MIROC-ESM-CHEM_2080_rp01000.tif':
        #     continue

        for idx, region in regions.iterrows():

            output = []

            gid_id = region[gid_level]
            scenario_name = os.path.basename(scenario)[:-4]

            # if not gid_id == 'MWI.13.12_1':
            #     continue

            filename = '{}_{}.csv'.format(gid_id, scenario_name)
            folder_out = os.path.join(DATA_PROCESSED, iso3, 'regional_data', gid_id, 'flood_scenarios')
            path_output = os.path.join(folder_out, filename)

            # if os.path.exists(path_output):
            #     continue

            filename = '{}.csv'.format(gid_id)
            folder = os.path.join(DATA_PROCESSED, iso3, 'sites', gid_level.lower())
            path = os.path.join(folder, filename)

            if not os.path.exists(path):
                continue

            sites = pd.read_csv(path)#[:1] #, crs='epsg:4326'

            failures = 0

            for idx, site in sites.iterrows():

                x = float(site['cellid4326'].split('_')[0])
                y = float(site['cellid4326'].split('_')[1])

                with rasterio.open(scenario) as src:

                    src.kwargs = {'nodata':255}

                    coords = [(x, y)]

                    depth = [sample[0] for sample in src.sample(coords)][0]

                    # fragility = query_fragility_curve(f_curve, depth)

                    # failure_prob = random.uniform(0, 1)

                    # failed = (1 if failure_prob < fragility else 0)

                    # if fragility > 0:
                    #     failures += 1

                    output.append({
                        # 'type': 'Feature',
                        # 'geometry': site['geometry'],
                        # 'properties': {
                        'radio': site['radio'],
                        'mcc': site['mcc'],
                        'net': site['net'],
                        'area': site['area'],
                        'cell': site['cell'],
                        'gid_level': gid_level,
                        'gid_id': region[gid_level],
                        'cellid4326': site['cellid4326'],
                        'cellid3857': site['cellid3857'],
                        'depth': depth,
                            # 'scenario': scenario_name,
                            # 'fragility': fragility,
                            # 'fail_prob': failure_prob,
                            # 'failure': failed,
                            # 'cost_usd': round(100000 * fragility),
                            # 'cell_id': site['cell_id'],
                        # },
                    })

            if len(output) == 0:
                return

            if not os.path.exists(folder_out):
                os.makedirs(folder_out)

            output = pd.DataFrame(output)

            output.to_csv(path_output, index=False)

    return


def query_hazard_layers2(country, regions, technologies, scenarios):
    """
    Query each hazard layer and estimate fragility.

    """
    iso3 = country['iso3']
    name = country['country']
    regional_level = country['lowest']
    gid_level = 'GID_{}'.format(1) #regional_level

    filename = 'fragility_curve.csv'
    path_fragility = os.path.join(DATA_RAW, filename)
    f_curve = pd.read_csv(path_fragility)
    f_curve = f_curve.to_dict('records')

    regions = get_regions(country, 1)#[:50]
    regions = regions[regions['GID_1'] == 'AFG.14.6_1']

    for scenario in tqdm(scenarios):

        # if not scenario == 'data\processed\MWI\hazards\inunriver_rcp8p5_MIROC-ESM-CHEM_2080_rp01000.tif':
        #     continue

        output = []

        for idx, region in regions.iterrows():

            gid_id = region[gid_level]
            scenario_name = os.path.basename(scenario)[:-4]

            # if not gid_id == 'MWI.13.12_1':
            #     continue

            filename = '{}_{}.csv'.format(gid_id, scenario_name)
            folder_out = os.path.join(DATA_PROCESSED, iso3, 'regional_data', gid_id, 'scenarios')
            path_output = os.path.join(folder_out, filename)

            if os.path.exists(path_output):
                continue

            filename = '{}.csv'.format(gid_id)
            folder = os.path.join(DATA_PROCESSED, iso3, 'sites', gid_level.lower())
            path = os.path.join(folder, filename)

            if not os.path.exists(path):
                continue

            sites = pd.read_csv(path)#[:1], crs='epsg:4326'

            failures = 0

            for idx, site in sites.iterrows():

                x = float(site['cellid4326'].split('_')[0])
                y = float(site['cellid4326'].split('_')[1])

                with rasterio.open(scenario) as src:

                    src.kwargs = {'nodata':255}

                    coords = [(x, y)]

                    depth = [sample[0] for sample in src.sample(coords)][0]

                    # fragility = query_fragility_curve(f_curve, depth)

                    # failure_prob = random.uniform(0, 1)

                    # failed = (1 if failure_prob < fragility else 0)

                    # if fragility > 0:
                    #     failures += 1

                    output.append({
                        # 'type': 'Feature',
                        # 'geometry': site['geometry'],
                        # 'properties': {
                        'radio': site['radio'],
                        'mcc': site['mcc'],
                        'net': site['net'],
                        'area': site['area'],
                        'cell': site['cell'],
                        'gid_level': gid_level,
                        'gid_id': region[gid_level],
                        'depth': depth,
                            # 'scenario': scenario_name,
                            # 'fragility': fragility,
                            # 'fail_prob': failure_prob,
                            # 'failure': failed,
                            # 'cost_usd': round(100000 * fragility),
                            # 'cell_id': site['cell_id'],
                        # },
                    })

        if len(output) == 0:
            return

        if not os.path.exists(folder_out):
            os.makedirs(folder_out)

        output = pd.DataFrame(output)
        output.to_csv(path_output)

    return


def query_fragility_curve(f_curve, depth):
    """
    Query the fragility curve.
    """
    if depth < 0:
        return 0

    for item in f_curve:
        if item['depth_lower_m'] <= depth < item['depth_upper_m']:
            return item['fragility']
        else:
            continue
    print('fragility curve failure: {}'.format(depth))
    return 0


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

    # if os.path.exists(path_output):
    #     return

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
    output = output.drop_duplicates()

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
    output = output.drop_duplicates()

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
    output = output.drop_duplicates()

    if not os.path.exists(folder_out):
        os.mkdir(folder_out)

    output.to_csv(path_output, index=False)

    return


def site_damage_impacts(country, technologies, scenarios):
    """
    Estimate coverage.

    Aqueduct flood scenarios as structured as follows:

    floodtype_climatescenario_subsidence_year_returnperiod_projection

    """
    iso3 = country['iso3']

    filename = 'sites_affected_by_failures_{}.csv'.format(iso3)
    folder_out = os.path.join(RESULTS)
    path_output = os.path.join(folder_out, filename)

    # if not os.path.exists(path_output):
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

        if returnperiod == 'rp01000' or returnperiod == 'rp1000':
            returnperiod = '1000-year'
        elif returnperiod == 'rp00500' or returnperiod == 'rp0500':
            returnperiod = '500-year'
        elif returnperiod == 'rp00250' or returnperiod == 'rp0250':
            returnperiod = '250-year'
        elif returnperiod == 'rp00100' or returnperiod == 'rp0100':
            returnperiod = '100-year'
        else:
            print('Return period not recognized {}'.format(returnperiod))

        for technology in technologies:

            filename = 'sites_{}_{}.csv'.format(technology, scenario)
            folder_in = os.path.join(DATA_PROCESSED, iso3, 'failed_sites')
            path_in = os.path.join(folder_in, filename)

            if not os.path.exists(path_in):
                continue
            data = pd.read_csv(path_in)

            affected_sites = 0
            cost = 0
            for idx, item in data.iterrows():
                if int(item['fragility']) > 0:
                    affected_sites += 1
                    cost += (100000 * item['fragility'])

            output.append({
                'floodtype': floodtype,
                'climatescenario': climatescenario,
                'subsidence': subsidence,
                'year': year,
                'returnperiod': returnperiod,
                'projection': projection,
                'affected_sites': affected_sites,
                'cost': cost,
                'technology': technology,
                'scenario': scenario,
            })

    output = pd.DataFrame(output)
    output = output.drop_duplicates()

    if not os.path.exists(folder_out):
        os.mkdir(folder_out)

    output.to_csv(path_output, index=False)

    return


if __name__ == "__main__":

    import cProfile
    # cProfile.run('foo()')

    countries = get_countries()[:50]

    for idx, country in countries.iterrows():

        if not country['iso3'] == 'IRL':
            continue

        print('-Working on {}'.format(country['iso3']))

        regions = get_regions(country, 1)#[:50]
        scenarios = get_scenarios(country)#[:10]

        process_flooding_layers(country, scenarios)

        # cProfile.run('query_hazard_layers(country, regions, technologies, scenarios)', 'profile.log')
        query_hazard_layers(country, regions, technologies, scenarios)
        # # cProfile.run('query_hazard_layers2(country, regions, technologies, scenarios)')


        # query_hazard_layers2(country, regions, technologies, scenarios)

        # econ_interim_impacts(country, technologies, scenarios)

        # econ_final_impacts(country)

        # coverage_interim_impacts(country, regions, technologies, scenarios)

        # coverage_final_impacts(country)

        # coverage_estimation_using_failures(country, regions, technologies, scenarios)

        # site_damage_impacts(country, technologies, scenarios)
