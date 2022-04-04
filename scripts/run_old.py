"""
Script to estimate population coverage.

Written by Ed Oughton.

February 2022.

"""
import os
import configparser
import random
import glob
import pandas as pd
import geopandas as gpd
import rasterio
from tqdm import tqdm

from misc import technologies, get_countries, get_regions, get_scenarios

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW = os.path.join(BASE_PATH, 'raw')
DATA_PROCESSED = os.path.join(BASE_PATH, 'processed')


def query_hazard_layers(country, region, technology, scenario):
    """
    Query each hazard layer and estimate fragility.

    """
    iso3 = country['iso3']
    name = country['country']
    regional_level = country['gid_region']
    gid_level = 'GID_{}'.format(regional_level)
    gid_id = region[gid_level]
    scenario_name = os.path.basename(scenario)

    filename = 'fragility_curve.csv'
    path_fragility = os.path.join(DATA_RAW, filename)
    f_curve = pd.read_csv(path_fragility)
    f_curve = f_curve.to_dict('records')

    filename = '{}_{}_{}.shp'.format(gid_id, technology, scenario_name)
    folder_out = os.path.join(DATA_PROCESSED, iso3, 'regional_data', gid_id, technology)
    path_output = os.path.join(folder_out, filename)

    if not os.path.exists(folder_out):
        os.makedirs(folder_out)

    if os.path.exists(path_output):
        return

    filename = '{}_{}.shp'.format(technology, gid_id)
    folder = os.path.join(DATA_PROCESSED, iso3, 'sites', technology)
    path = os.path.join(folder, filename)

    if not os.path.exists(path):
        return

    sites = gpd.read_file(path, crs='epsg:3857')#[:1]
    sites = sites.to_crs(4326)

    output = []

    failures = 0

    for idx, site in sites.iterrows():

        with rasterio.open(scenario) as src:
            src.kwargs = {'nodata':255}

            coords = [(site['geometry'].x, site['geometry'].y)]

            depth = [sample[0] for sample in src.sample(coords)][0]

            fragility = query_fragility_curve(f_curve, depth)

            failure_prob = random.uniform(0, 1)

            failed = (1 if failure_prob < fragility else 0)

            if fragility > 0:
                failures += 1

            output.append({
                'type': 'Feature',
                'geometry': site['geometry'],
                'properties': {
                    'radio': site['radio'],
                    'mcc': site['mcc'],
                    'net': site['net'],
                    'area': site['area'],
                    'cell': site['cell'],
                    'gid_level': gid_level,
                    'gid_id': region[gid_level],
                    'depth': depth,
                    'scenario': scenario_name,
                    'fragility': fragility,
                    'fail_prob': failure_prob,
                    'failure': failed,
                    # 'cell_id': site['cell_id'],
                }
            })

    if len(output) == 0:
        return

    if not os.path.exists(folder_out):
        os.makedirs(folder_out)

    output = gpd.GeoDataFrame.from_features(output, crs='epsg:4326')
    output.to_file(path_output, crs=crs)

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


def estimate_coverage(country, region, technology, scenario):
    """
    Estimate population coverage by region.

    """
    iso3 = country['iso3']
    name = country['country']
    regional_level = country['gid_region']
    gid_level = 'GID_{}'.format(regional_level)
    gid_id = region[gid_level]
    scenario_name = os.path.basename(scenario)

    filename = '{}_sinr_lut.csv'.format(technology)
    folder = os.path.join(DATA_PROCESSED, iso3, 'regional_data', gid_id)
    path_in = os.path.join(folder, filename)
    sinr_lut = pd.read_csv(path_in)
    print(sinr_lut)

    # filename = '{}_{}_{}.shp'.format(gid_id, technology, scenario_name)
    # folder = os.path.join(DATA_PROCESSED, iso3, 'regional_data', gid_id, technology)
    # path_in = os.path.join(folder, filename)

    # if not os.path.exists(path_in):
    #     return

    # output = []

    # sites = gpd.read_file(path_in, crs='epsg:4326')

    # for idx, site in sites.iterrows():
    #     print(site)
    #     gid_id = item['GID_id']
    #     area_km2 = item['area_km2']
    #     population_total = item['population_total']

    #     coverage = {}

    #     filename = '{}_{}_{}.shp'.format(technology, gid_id, scenario)
    #     folder = os.path.join(DATA_PROCESSED, iso3, 'scenarios', scenario, technology, 'buffer')
    #     path_in = os.path.join(folder, filename)

    #     if not os.path.exists(path_in):
    #         continue

    #     buffer = gpd.read_file(path_in, crs='epsg:3857')
    #     covered_area_km2 = round(buffer.area / 1e6).values[0]

    #     coverage = round((covered_area_km2 / area_km2)*100)

    #     output.append({
    #         'GID_0': item['GID_0'],
    #         'GID_id': item['GID_id'],
    #         'GID_level': item['GID_level'],
    #         'population_total': item['population_total'],
    #         'population_over_10': item['population_over_10'],
    #         'area_km2': item['area_km2'],
    #         'population_km2': item['population_km2'],
    #         'population_over_10yrs_km2': item['population_over_10yrs_km2'],
    #         'scenario': scenario,
    #         'technology': technology,
    #         'sites': buffer['sites'].values[0],
    #         'sites_fail': buffer['sites_fail'].values[0],
    #         'pop_coverage_perc': coverage,
    #         'pop_coverage': coverage_pop(coverage, population_total),
    #     })

    # if not len(output) > 0:
    #     return

    # output = pd.DataFrame(output)

    # filename = 'regions_{}_{}.csv'.format(technology, scenario)
    # folder_out = os.path.join(DATA_PROCESSED, iso3, 'scenarios', scenario, technology)
    # path_output = os.path.join(folder_out, filename)

    # output.to_csv(path_output, index=False)

    return


def coverage_pop(coverage, population_total):
    """
    Calculate the population coverage.

    """
    output = round(population_total * (coverage/100))

    return output


def write_out_site_failures(country, region, technology, scenario):
    """
    Write out site failures to .csv.

    """
    iso3 = country['iso3']
    name = country['country']
    regional_level = country['gid_region']
    gid_level = 'GID_{}'.format(regional_level)
    gid_id = region[gid_level]
    scenario_name = os.path.basename(scenario)

    output = []

    filename = '{}_{}_{}.shp'.format(gid_id, technology, scenario_name)
    folder = os.path.join(DATA_PROCESSED, iso3, 'regional_data', gid_id, technology)
    path_in = os.path.join(folder, filename)

    if not os.path.exists(path_in):
        return

    sites = gpd.read_file(path_in, crs='epsg:4326')

    for idx, site in sites.iterrows():

        output.append({
            'GID_0': region['GID_0'],
            'GID_id': region[gid_level],
            'GID_level': gid_level,
            'scenario': site['scenario'],
            'technology': site['radio'],
            'depth': site['depth'],
            'fragility': site['fragility'],
            'fail_prob': site['fail_prob'],
            'failure': site['failure'],
            'lon': site['geometry'].x,
            'lat': site['geometry'].y,
        })

    if not len(output) > 0:
        return

    output = pd.DataFrame(output)

    filename = '{}_{}_{}.csv'.format(gid_id, technology, scenario_name)
    folder_out = os.path.join(DATA_PROCESSED, iso3, 'regional_data', gid_id, technology)
    path_output = os.path.join(folder_out, filename)

    output.to_csv(path_output, index=False)

    return


def collect_country_results(country, scenarios, technologies):
    """
    Collect country results.

    """
    iso3 = country['iso3']
    name = country['country']
    regional_level = country['gid_region']

    data_types = [
        # 'regions',
        'sites'
    ]

    for data_type in data_types:

        output = []

        for scenario in tqdm(scenarios):

            for technology in technologies:

                scenario_name = os.path.basename(scenario)
                filename = '{}_{}_{}.csv'.format(data_type, technology, scenario_name)
                folder = os.path.join(DATA_PROCESSED, iso3, 'scenarios', scenario_name, technology)
                path = os.path.join(folder, filename)

                if not os.path.exists(path):
                    continue

                data = pd.read_csv(path)

                data = data.to_dict('records')#[:1]

                output = output + data

        output = pd.DataFrame(output)

        filename = '{}_{}.csv'.format(data_type, iso3)
        folder_out = os.path.join(BASE_PATH, '..', 'results')
        path_output = os.path.join(folder_out, filename)

        if not os.path.exists(folder_out):
            os.mkdir(folder_out)

        output.to_csv(path_output, index=False)

    return


if __name__ == '__main__':

    crs = 'epsg:4326'
    os.environ['GDAL_DATA'] = ("C:\\Users\edwar\\Anaconda3\\Library\\share\\gdal")
    random.seed(44)

    countries = get_countries()

    for idx, country in countries.iterrows():

        if not country['iso3'] == 'GHA':
            continue

        print('Working on {}'.format(country['iso3']))

        regions = get_regions(country)

        for idx, region in tqdm(regions.iterrows(), total=regions.shape[0]):

            GID_level = 'GID_{}'.format(country['lowest'])
            gid_id = region[GID_level]

            if not gid_id == 'GHA.9.7_1': #'GHA.1.12_1':
                continue

            hazard_dir = os.path.join(DATA_PROCESSED, country['iso3'], 'hazards')
            scenarios  = get_scenarios(hazard_dir)
            # scenarios = pd.DataFrame(scenarios)
            # path_out = os.path.join(DATA_PROCESSED, country['iso3'], 'scenarios', 'scenarios.csv')
            # scenarios.to_csv(path_out,index=False)

            for technology in technologies:

                if not technology == 'GSM':
                    continue

                for scenario in tqdm(scenarios):

                    # if not os.path.basename(scenario) == 'inunriver_rcp4p5_MIROC-ESM-CHEM_2080_rp00500.tif':
                    #     continue

                    # print('  {} - {}'.format(technology, scenario))

                    # if not scenario == 'baseline':
                    # query_hazard_layers(country, region, technology, scenario)

                    estimate_coverage(country, region, technology, scenario)

                    # write_out_site_failures(country, region, technology, scenario)



        #     print('Collecting country results')
        #     collect_country_results(country, scenarios, technologies)

        # # # print('Complete')
