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

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW = os.path.join(BASE_PATH, 'raw')
DATA_PROCESSED = os.path.join(BASE_PATH, 'processed')


def get_scenarios(hazard_dir):
    """

    """
    output = []

    scenarios = glob.glob(os.path.join(hazard_dir, "*.tif"))#[:3]

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


def query_hazard_layers(country, scenario, technology):
    """
    Query each hazard layer and estimate fragility.

    """
    iso3 = country['iso3']
    name = country['country']
    regional_level = country['gid_region']

    filename = 'regions_{}_{}.shp'.format(regional_level, iso3)
    folder = os.path.join(DATA_PROCESSED, iso3, 'regions')
    path = os.path.join(folder, filename)
    regions = gpd.read_file(path, crs=crs)#[:1]

    # filename = '{}.tif'.format(scenario)
    # folder = os.path.join(DATA_PROCESSED, iso3, 'hazards')
    # path_hazard = os.path.join(folder, filename)
    scenario_name = os.path.basename(scenario)

    filename = 'fragility_curve.csv'
    path_fragility = os.path.join(DATA_RAW, filename)
    f_curve = pd.read_csv(path_fragility)

    f_curve = f_curve.to_dict('records')

    for idx, region in regions.iterrows():

        gid_level = 'GID_{}'.format(regional_level)
        gid_id = region[gid_level]

        # if not gid_id == 'GHA.9.7_1':
        #     continue

        filename = '{}_{}_{}.shp'.format(technology, gid_id, scenario_name)
        folder_out = os.path.join(DATA_PROCESSED, iso3, 'scenarios', scenario_name, technology)
        path_output = os.path.join(folder_out, filename)

        if os.path.exists(path_output):
            continue

        output = []

        filename = '{}_{}.shp'.format(technology, gid_id)
        folder = os.path.join(DATA_PROCESSED, iso3, 'sites', technology)
        path = os.path.join(folder, filename)

        if not os.path.exists(path):
            continue

        sites = gpd.read_file(path, crs=crs)#[:1]

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
                    }
                })

        if len(output) == 0:
            continue

        if not os.path.exists(folder_out):
            os.makedirs(folder_out)

        output = gpd.GeoDataFrame.from_features(output, crs=crs)

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


def generate_coverage_polygons(country, scenario, technology):
    """
    Buffer each site. Merge overlapping site boundaries.
    Clip to each local statistical area.

    """
    iso3 = country['iso3']
    name = country['country']
    regional_level = country['gid_region']

    filename = 'regions_{}_{}.shp'.format(regional_level, iso3)
    folder = os.path.join(DATA_PROCESSED, iso3, 'regions')
    path = os.path.join(folder, filename)
    regions = gpd.read_file(path, crs=crs)#[:1]

    for idx, region in regions.iterrows():

        gid_level = 'GID_{}'.format(regional_level)
        gid_id = region[gid_level]

        filename = '{}_{}_{}.shp'.format(technology, gid_id, scenario)
        folder_out = os.path.join(DATA_PROCESSED, iso3, 'scenarios', scenario, technology, 'buffer')
        path_output = os.path.join(folder_out, filename)

        # if os.path.exists(path_output):
        #     continue

        if scenario == 'baseline':
            filename = '{}_{}.shp'.format(technology, gid_id)
            folder = os.path.join(DATA_PROCESSED, iso3, 'sites', technology)
            path = os.path.join(folder, filename)
        else:
            filename = '{}_{}_{}.shp'.format(technology, gid_id, scenario)
            folder = os.path.join(DATA_PROCESSED, iso3, 'scenarios', scenario, technology)
            path = os.path.join(folder, filename)

        if not os.path.exists(path):
            continue

        sites = gpd.read_file(path, crs=crs)#[:1]

        total_sites = len(sites)

        # Remove failed sites
        if not scenario == 'baseline':
            sites = sites.loc[sites['failure'] == 0]

        sites.to_crs(epsg=3857, inplace=True)

        sites['geometry'] = sites['geometry'].buffer(10000)
        geoms = sites.geometry.unary_union
        buffers = gpd.GeoDataFrame(geometry=[geoms], crs=3857)

        if buffers['geometry'].values[0] is None:
            continue

        buffers = buffers.explode(index_parts=False).reset_index(drop=True)

        m_region = gpd.GeoDataFrame(gpd.GeoSeries(region['geometry']))
        m_region = m_region.rename(columns={0:'geometry'}).set_geometry('geometry')
        m_region = m_region.set_crs(epsg=4326)
        m_region.to_crs(epsg=3857, inplace=True)

        buffers = buffers.overlay(m_region, how='intersection')
        buffers['sites'] = len(sites)
        buffers['sites_fail'] = total_sites - len(sites)

        if len(buffers) == 0:
            continue

        if not os.path.exists(folder_out):
            os.makedirs(folder_out)

        buffers.to_file(path_output, crs='epsg:3857')

    return


def estimate_coverage_by_region(country, scenario, technology):
    """
    Estimate population coverage by region.

    """
    iso3 = country['iso3']
    name = country['country']
    regional_level = country['gid_region']

    filename = 'regional_data.csv'
    folder = os.path.join(DATA_PROCESSED, iso3)
    path = os.path.join(folder, filename)
    regional_data = pd.read_csv(path)#[:5]

    output = []

    for idx, item in regional_data.iterrows():

        gid_id = item['GID_id']
        area_km2 = item['area_km2']
        population_total = item['population_total']

        coverage = {}

        filename = '{}_{}_{}.shp'.format(technology, gid_id, scenario)
        folder = os.path.join(DATA_PROCESSED, iso3, 'scenarios', scenario, technology, 'buffer')
        path_in = os.path.join(folder, filename)

        if not os.path.exists(path_in):
            continue

        buffer = gpd.read_file(path_in, crs='epsg:3857')
        covered_area_km2 = round(buffer.area / 1e6).values[0]

        coverage = round((covered_area_km2 / area_km2)*100)

        output.append({
            'GID_0': item['GID_0'],
            'GID_id': item['GID_id'],
            'GID_level': item['GID_level'],
            'population_total': item['population_total'],
            'population_over_10': item['population_over_10'],
            'area_km2': item['area_km2'],
            'population_km2': item['population_km2'],
            'population_over_10yrs_km2': item['population_over_10yrs_km2'],
            'scenario': scenario,
            'technology': technology,
            'sites': buffer['sites'].values[0],
            'sites_fail': buffer['sites_fail'].values[0],
            'pop_coverage_perc': coverage,
            'pop_coverage': coverage_pop(coverage, population_total),
        })

    if not len(output) > 0:
        return

    output = pd.DataFrame(output)

    filename = 'regions_{}_{}.csv'.format(technology, scenario)
    folder_out = os.path.join(DATA_PROCESSED, iso3, 'scenarios', scenario, technology)
    path_output = os.path.join(folder_out, filename)

    output.to_csv(path_output, index=False)

    return


def coverage_pop(coverage, population_total):
    """
    Calculate the population coverage.

    """
    output = round(population_total * (coverage/100))

    return output


def write_out_site_failures(country, scenario, technology):
    """
    Write out site failures to .csv.

    """
    iso3 = country['iso3']
    name = country['country']
    regional_level = country['gid_region']

    filename = 'regional_data.csv'
    folder = os.path.join(DATA_PROCESSED, iso3)
    path = os.path.join(folder, filename)
    regional_data = pd.read_csv(path)#[:5]

    scenario_name = os.path.basename(scenario)

    output = []

    for idx, item in regional_data.iterrows():

        gid_id = item['GID_id']
        area_km2 = item['area_km2']
        population_total = item['population_total']

        filename = '{}_{}_{}.shp'.format(technology, gid_id, scenario_name)
        folder = os.path.join(DATA_PROCESSED, iso3, 'scenarios', scenario_name, technology)
        path_in = os.path.join(folder, filename)

        if not os.path.exists(path_in):
            continue

        sites = gpd.read_file(path_in, crs='epsg:4326')

        for idx, site in sites.iterrows():

            output.append({
                'GID_0': item['GID_0'],
                'GID_id': item['GID_id'],
                'GID_level': item['GID_level'],
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

    filename = 'sites_{}_{}.csv'.format(technology, scenario_name)
    folder_out = os.path.join(DATA_PROCESSED, iso3, 'scenarios', scenario_name, technology)
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

    filename = "countries.csv"
    path = os.path.join(DATA_RAW, filename)
    countries = pd.read_csv(path, encoding='latin-1')

    technologies = [
        'GSM',
        'UMTS',
        'LTE',
        'NR',
    ]

    for idx, country in countries.iterrows():

        if not country['iso3'] == 'GHA':
            continue

        iso3 = country['iso3']

        print('Working on {}'.format(iso3))

        hazard_dir = os.path.join(DATA_PROCESSED, iso3, 'hazards')
        scenarios  = get_scenarios(hazard_dir)
        # scenarios = pd.DataFrame(scenarios)
        # scenarios.to_csv(os.path.join(DATA_PROCESSED, iso3, 'scenarios', 'scenarios.csv'),index=False)

        for scenario in tqdm(scenarios):
            # print(scenario)
            for technology in technologies:

                print('  {} - {}'.format(technology, scenario))

                if not scenario == 'baseline':
                    # print('Querying hazard layers')
                    query_hazard_layers(country, scenario, technology)

    #             print('Generating coverage polygons')
    #             generate_coverage_polygons(country, scenario, technology)

    #             print('Estimating coverage')
    #             estimate_coverage_by_region(country, scenario, technology)

                # print('Estimating coverage')
                write_out_site_failures(country, scenario, technology)

        print('Collecting country results')
        collect_country_results(country, scenarios, technologies)

    # print('Complete')
