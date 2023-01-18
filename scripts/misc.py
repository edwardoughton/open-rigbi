"""
Miscellaneous model inputs.

"""
import os
import configparser
import glob
import pandas as pd
import geopandas as gpd
# from shapely.ops import transform
from shapely.geometry import shape, Point, mapping, LineString, MultiPolygon

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW = os.path.join(BASE_PATH, 'raw')
DATA_PROCESSED = os.path.join(BASE_PATH, 'processed')


params = {
        # 'number_of_satellites': 5040,
        'iterations': 100,
        'seed_value': 42,
        'mu': 2, #Mean of distribution
        'sigma': 10, #Standard deviation of distribution
        'dl_frequency': 8*10**9, #Downlink frequency in Hertz
        'dl_bandwidth': 0.1*10**9, #Downlink bandwidth in Hertz
        'speed_of_light': 3.0*10**8, #Speed of light in vacuum
        'power': 42, #dBw
        'antenna_gain': 18,
        'receiver_gain': 0,
        'earth_atmospheric_losses': 12, #Rain Attenuation
        'all_other_losses': 0.53, #All other losses
        'minimum_interference': -120, #Number of channels per satellite
        'functioning_sinr': 0,
        'number_of_cells': 3, #Number of cells to check distance to
}


technologies = [
    'GSM',
    'UMTS',
    'LTE',
    'NR',
]


def get_countries():
    """
    Get all countries.

    """
    filename = "countries.csv"
    path = os.path.join(DATA_RAW, filename)

    countries = pd.read_csv(path, encoding='latin-1')
    countries = countries[countries.Exclude == 0]
    countries = countries.sort_values(by=['iso3'], ascending=True)

    return countries#[:10]


def get_regions(country, region_type):
    """


    """
    if region_type == 'use_csv':
        filename = 'regions_{}_{}.shp'.format(
            country['lowest'],
            country['iso3']
        )
        folder = os.path.join(DATA_PROCESSED, country['iso3'], 'regions')
    elif region_type in [1, 2]:
        filename = 'regions_{}_{}.shp'.format(
            region_type,
            country['iso3']
        )
        folder = os.path.join(DATA_PROCESSED, country['iso3'], 'regions')
    elif region_type == 0:
        filename = 'national_outline.shp'
        folder = os.path.join(DATA_PROCESSED, country['iso3'])
    else:
        print("Did not recognize region_type arg provided to get_regions()")

    path = os.path.join(folder, filename)

    if not os.path.exists(path):
        print('Created this path as it did not exist: {}'.format(path))
        return []

    regions = gpd.read_file(path, crs='epsg:4326')#[:1]

    return regions


def get_scenarios():
    """

    """
    output = set()

    # hazard_dir = os.path.join(DATA_PROCESSED, country['iso3'], 'hazards', 'flooding')
    hazard_dir = os.path.join(DATA_RAW,  'flood_hazard')

    scenarios = glob.glob(os.path.join(hazard_dir, "*.tif"))#[:20]

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

    #mean_scenarios = generate_mean_scenarios(scenarios, return_periods)

    scenarios = scenarios #+ mean_scenarios

    for scenario in scenarios:

        if any(x in scenario for x in return_periods): #specify return periods

            if 'inuncoast' and 'wtsub' in scenario:
                #if 'historical' in scenario:
                #    if '2030' or '2050' or '2080' in scenario:
                #    continue
                if not 'hist' in scenario:
                    output.add(scenario)
                
            elif 'inunriver' in scenario: #and 'MIROC-ESM-CHEM'
                if not 'historical' in scenario:
                    output.add(scenario)
            else:
                continue

        if 'historical' in scenario:

            if any(x in scenario for x in return_periods): #specify return periods
                if 'inuncoast_historical_wtsub_hist' in scenario:
                    output.add(scenario)
                elif 'inunriver_historical' in scenario:
                    output.add(scenario)
                else:
                    continue

    output = list(output)
    output.sort() 
    return output#[:1]


def generate_mean_scenarios(scenarios, return_periods):
    """
    Generate mean scenario names.

    """
    output = []

    climate_scenarios = set()
    years = set()
    return_periods = set()

    for scenario in scenarios:

        if not 'inunriver' in scenario:
            continue

        basename = os.path.basename(scenario).replace('.tif', '')

        climate_scenario = basename.split('_')[1]
        if not 'historical' in climate_scenario:
            climate_scenarios.add(climate_scenario)

        year = basename.split('_')[3]
        if not any(x in year for x in ['1980', 'hist']):
            years.add(year)

        return_periods.add(basename.split('_')[4])

    for climate_scenario in list(climate_scenarios):
        for year in list(years):
            for return_period in list(return_periods):

                scenario = 'inunriver_{}_model-mean_{}_{}.tif'.format(
                    climate_scenario,
                    year,
                    return_period
                )

                scenario_path = os.path.join('data', 'raw', 'flood_hazard', scenario)

                output.append(scenario_path)

    return output


def process_country_shapes(iso3):
    """
    Creates a single national boundary for the desired country.

    Parameters
    ----------
    country : dict
        Contains all desired country information.

    """
    path = os.path.join(DATA_PROCESSED, iso3)

    if os.path.exists(os.path.join(path, 'national_outline.shp')):
        return 'Completed national outline processing'

    print('Processing country shapes')

    if not os.path.exists(path):
        os.makedirs(path)

    shape_path = os.path.join(path, 'national_outline.shp')

    path = os.path.join(DATA_RAW, 'gadm36_levels_shp', 'gadm36_0.shp')

    countries = gpd.read_file(path)

    single_country = countries[countries.GID_0 == iso3].reset_index()

    single_country = single_country.copy()
    single_country["geometry"] = single_country.geometry.simplify(
        tolerance=0.01, preserve_topology=True)

    single_country['geometry'] = single_country.apply(
        remove_small_shapes, axis=1)

    glob_info_path = os.path.join(DATA_RAW, 'countries.csv')
    load_glob_info = pd.read_csv(glob_info_path, encoding = "ISO-8859-1",
        keep_default_na=False)
    single_country = single_country.merge(
        load_glob_info, left_on='GID_0', right_on='iso3')

    single_country.to_file(shape_path, driver='ESRI Shapefile')

    return


def remove_small_shapes(x):
    """
    Remove small multipolygon shapes.

    Parameters
    ---------
    x : polygon
        Feature to simplify.

    Returns
    -------
    MultiPolygon : MultiPolygon
        Shapely MultiPolygon geometry without tiny shapes.

    """
    if x.geometry.type == 'Polygon':
        return x.geometry

    elif x.geometry.type == 'MultiPolygon':

        area1 = 0.01
        area2 = 50

        if x.geometry.area < area1:
            return x.geometry

        if x['GID_0'] in ['CHL','IDN']:
            threshold = 0.01
        elif x['GID_0'] in ['RUS','GRL','CAN','USA']:
            threshold = 0.01
        elif x.geometry.area > area2:
            threshold = 0.1
        else:
            threshold = 0.001

        new_geom = []
        for y in list(x['geometry'].geoms):
            if y.area > threshold:
                new_geom.append(y)

        return MultiPolygon(new_geom)


def process_regions(iso3, level):
    """
    Function for processing the lowest desired subnational
    regions for the chosen country.

    Parameters
    ----------
    country : dict
        Contains all desired country information.

    """
    regions = []

    for regional_level in range(1, int(level) + 1):

        filename = 'regions_{}_{}.shp'.format(regional_level, iso3)
        folder = os.path.join(DATA_PROCESSED, iso3, 'regions')
        path_processed = os.path.join(folder, filename)

        if os.path.exists(path_processed):
            continue

        print('Processing GID_{} region shapes'.format(regional_level))

        if not os.path.exists(folder):
            os.mkdir(folder)

        filename = 'gadm36_{}.shp'.format(regional_level)
        path_regions = os.path.join(DATA_RAW, 'gadm36_levels_shp', filename)
        regions = gpd.read_file(path_regions)

        regions = regions[regions.GID_0 == iso3]

        regions = regions.copy()
        regions["geometry"] = regions.geometry.simplify(
            tolerance=0.01, preserve_topology=True)

        regions['geometry'] = regions.apply(remove_small_shapes, axis=1)

        try:
            regions.to_file(path_processed, driver='ESRI Shapefile')
        except:
            print('Unable to write {}'.format(filename))
            pass

    return


if __name__ == '__main__':

    countries = get_countries()

    # for country in countries:
    #     print(country)

    scenarios = get_scenarios()

    for scenario in scenarios:
        print(scenario)
