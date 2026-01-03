"""
Miscellaneous model inputs.

This module provides helper functions and configuration required by the model,
including accessors for country and region datasets, hazard scenario selection,
and preprocessing of national and subnational administrative boundaries.

Written by Ed Oughton
February 2022
"""
import os
import configparser
import pandas as pd
import geopandas as gpd
from shapely.geometry import MultiPolygon

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW = os.path.join(BASE_PATH, '..', '..', 'data_raw')
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
    Read and return the list of included countries.

    Countries are loaded from ``countries.csv`` and filtered to those not
    marked for exclusion.

    Returns
    -------
    list of dict
        Country records as dictionaries.
    """
    filename = "countries.csv"
    path = os.path.join(BASE_PATH, filename)

    countries = pd.read_csv(path, encoding='latin-1')
    countries = countries[countries.Exclude == 0]
    countries = countries.to_dict('records')

    return countries


def get_regions(country, region_type):
    """
    Read and return region geometries for a country and region type.

    Depending on ``region_type``, this function loads either the national
    outline or a subnational regions layer from the processed data directory.

    Parameters
    ----------
    country : dict
        Country metadata dictionary containing at least ``iso3`` and, when
        ``region_type`` is ``'use_csv'``, the key ``lowest``.
    region_type : int or str
        Region selector. Use 0 for national outline, 1 or 2 for subnational
        region layers, or ``'use_csv'`` to load the country-defined lowest
        processed level.

    Returns
    -------
    list of dict
        Region records as dictionaries. Returns an empty list if the expected
        file is missing.
    """
    if region_type == 'use_csv':
        filename = 'regions_{}_{}.gpkg'.format(
            country['lowest'],
            country['iso3']
        )
        folder = os.path.join(DATA_PROCESSED, country['iso3'], 'regions')
    elif region_type in [1, 2]:
        filename = 'regions_{}_{}.gpkg'.format(
            region_type,
            country['iso3']
        )
        folder = os.path.join(DATA_PROCESSED, country['iso3'], 'regions')
    elif region_type == 0:
        filename = 'national_outline.gpkg'
        folder = os.path.join(DATA_PROCESSED, country['iso3'])
    else:
        print("Did not recognize region_type arg provided to get_regions()")

    path = os.path.join(folder, filename)

    if not os.path.exists(path):
        print('This path did not exist/load: {}'.format(path))
        return []

    regions = gpd.read_file(path)#[:1]
    regions = regions.to_dict('records')

    return regions


def get_scenarios():
    """
    Build and return the set of flood hazard scenario identifiers.

    Scenario identifiers are derived from the filenames in the flood hazard
    directory and filtered to include specific return periods and hazard types.

    Returns
    -------
    list of str
        Scenario identifiers.
    """
    output = set()

    hazard_dir = os.path.join(DATA_RAW,  'flood_hazard')
    scenarios = os.listdir(os.path.join(hazard_dir))#[:20]
    scenarios = [i.replace('.tif','') for i in scenarios]
    scenarios = [i.replace('.aux','') for i in scenarios]
    scenarios = [i.replace('.xml','') for i in scenarios]

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

            # if 'inunriver' in scenario:
            #    continue
            # if 'inuncoast' in scenario:
            #    continue

            if 'inuncoast' and 'wtsub' in scenario:
                #if 'historical' in scenario:
                #    if '2030' or '2050' or '2080' in scenario:
                #    continue
                # if not 'perc' in scenario:
                #     continue
                if not 'hist' in scenario:
                    output.add(scenario)

            if 'inunriver' in scenario: # and 'MIROC-ESM-CHEM' in scenario:

                # if '00IPSL' in scenario:
                #     continue
                # if 'GFDL' in scenario:
                #     continue
                # if 'NorESM1' in scenario:
                #     continue
                if not 'historical' in scenario:
                    output.add(scenario)

        if 'historical' in scenario:

            if any(x in scenario for x in return_periods): #specify return periods
                if 'inuncoast_historical_wtsub_hist' in scenario:
                    output.add(scenario)
                elif 'inunriver_historical' in scenario:
                    output.add(scenario)
                else:
                    continue

    output = list(output)

    return output


def get_tropical_storm_scenarios():
    """
    Build and return the set of tropical storm scenario identifiers.

    Scenario identifiers are derived from the filenames in the storm hazard
    directory and filtered by return period and other naming conventions.

    Returns
    -------
    list of str
        Scenario identifiers in sorted order.
    """
    output = set()

    hazard_dir = os.path.join(BASE_PATH, 'raw', 'storm_data')

    scenarios = os.listdir(os.path.join(hazard_dir))#[:20]
    scenarios = [i.replace('.tif', '') for i in scenarios]

    return_periods = [
        # "10_YR_RP",
        "50_YR_RP",
        "100_YR_RP",
        "200_YR_RP",
        "500_YR_RP",
        "1000_YR_RP",
        "10000_YR_RP",
    ]

    for scenario in scenarios:

        if 'xml' in scenario:
            continue

        if any(x in scenario for x in return_periods): #specify return periods

            # if not 'constant' in scenario: 
            #     continue
            # if 'HadGEM3' in scenario:
            #     continue

            output.add(scenario)

    output = list(output)
    output.sort()
 
    return output#[:1]


def process_country_shapes(iso3):
    """
    Create and write a simplified national boundary for a country.

    The national boundary is extracted from the GADM level 0 dataset, simplified,
    and written as ``national_outline.gpkg`` in the processed data directory.

    Parameters
    ----------
    iso3 : str
        Three-letter ISO country code.
    """
    folder = os.path.join(DATA_PROCESSED, iso3)
    path_out = os.path.join(folder, 'national_outline.gpkg')

    if os.path.exists(path_out):
        return 'Completed national outline processing'

    print('Processing country shapes')

    if not os.path.exists(folder):
        os.makedirs(folder)

    path = os.path.join(DATA_RAW, 'gadm36_levels_shp', 'gadm36_0.shp')
    countries = gpd.read_file(path)
    single_country = countries[countries.GID_0 == iso3].reset_index()

    single_country = single_country.copy()
    single_country["geometry"] = single_country.geometry.simplify(
        tolerance=0.01, preserve_topology=True)

    single_country['geometry'] = single_country.apply(
        remove_small_shapes, axis=1)

    glob_info_path = os.path.join(BASE_PATH, 'countries.csv')
    load_glob_info = pd.read_csv(glob_info_path, encoding = "ISO-8859-1",
        keep_default_na=False)
    single_country = single_country.merge(
        load_glob_info, left_on='GID_0', right_on='iso3')

    single_country.to_file(path_out, driver='GPKG')

    return


def remove_small_shapes(x):
    """
    Remove small multipolygon components from a feature geometry.

    Parameters
    ----------
    x : polygon
        Feature to simplify.

    Returns
    -------
    shapely.geometry.base.BaseGeometry
        Shapely geometry with small polygon components removed.
    """
    if x.geometry.geom_type == 'Polygon':
        return x.geometry

    elif x.geometry.geom_type == 'MultiPolygon':

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
    Process and write subnational region boundaries for a country.

    This function reads GADM administrative levels from 1 up to ``level``,
    simplifies geometries, removes small shapes, and writes each level to a
    GeoPackage in the processed data directory.

    Parameters
    ----------
    iso3 : str
        Three-letter ISO country code.
    level : int
        Maximum GADM administrative level to process.
    """
    regions = []

    for regional_level in range(1, int(level) + 1):

        filename = 'regions_{}_{}.gpkg'.format(regional_level, iso3)
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
            tolerance=0.003, preserve_topology=True)

        regions['geometry'] = regions.apply(remove_small_shapes, axis=1)

        try:
            regions.to_file(path_processed, driver='GPKG')
        except:
            print('Unable to write {}'.format(filename))
            pass

    return


def get_f_curves():
    """
    Return flood fragility curves.

    Returns
    -------
    list of dict
        Fragility curve records with depth ranges and associated damage ratios.
    """
    return [
    {'depth_lower_m': 0.0, 'depth_upper_m': 0.3, 'damage': 0.25, 'scenario': 'baseline', 'source': 'kok_et_al_2004'}, 
    {'depth_lower_m': 0.3, 'depth_upper_m': 1.0, 'damage': 0.5, 'scenario': 'baseline', 'source': 'kok_et_al_2004'}, 
    {'depth_lower_m': 1.0, 'depth_upper_m': 1.5, 'damage': 0.65, 'scenario': 'baseline', 'source': 'kok_et_al_2004'}, 
    {'depth_lower_m': 1.5, 'depth_upper_m': 2.0, 'damage': 0.8, 'scenario': 'baseline', 'source': 'kok_et_al_2004'}, 
    {'depth_lower_m': 2.0, 'depth_upper_m': 2.5, 'damage': 1.0, 'scenario': 'baseline', 'source': 'kok_et_al_2004'}, 
    {'depth_lower_m': 2.5, 'depth_upper_m': 3.0, 'damage': 1.0, 'scenario': 'baseline', 'source': 'kok_et_al_2004'}, 
    {'depth_lower_m': 3.0, 'depth_upper_m': 4.0, 'damage': 1.0, 'scenario': 'baseline', 'source': 'kok_et_al_2004'}, 
    {'depth_lower_m': 4.0, 'depth_upper_m': 5.0, 'damage': 1.0, 'scenario': 'baseline', 'source': 'kok_et_al_2004'}, 
    {'depth_lower_m': 0.0, 'depth_upper_m': 0.3, 'damage': 0.13, 'scenario': 'low', 'source': 'kok_et_al_2004'}, 
    {'depth_lower_m': 0.3, 'depth_upper_m': 1.0, 'damage': 0.25, 'scenario': 'low', 'source': 'kok_et_al_2004'}, 
    {'depth_lower_m': 1.0, 'depth_upper_m': 1.5, 'damage': 0.33, 'scenario': 'low', 'source': 'kok_et_al_2004'}, 
    {'depth_lower_m': 1.5, 'depth_upper_m': 2.0, 'damage': 0.4, 'scenario': 'low', 'source': 'kok_et_al_2004'}, 
    {'depth_lower_m': 2.0, 'depth_upper_m': 2.5, 'damage': 0.5, 'scenario': 'low', 'source': 'kok_et_al_2004'}, 
    {'depth_lower_m': 2.5, 'depth_upper_m': 3.0, 'damage': 0.6, 'scenario': 'low', 'source': 'kok_et_al_2004'}, 
    {'depth_lower_m': 3.0, 'depth_upper_m': 4.0, 'damage': 0.8, 'scenario': 'low', 'source': 'kok_et_al_2004'}, 
    {'depth_lower_m': 4.0, 'depth_upper_m': 5.0, 'damage': 1.0, 'scenario': 'low', 'source': 'kok_et_al_2004'}, 
    {'depth_lower_m': 0.0, 'depth_upper_m': 0.3, 'damage': 0.5, 'scenario': 'high', 'source': 'kok_et_al_2004'}, 
    {'depth_lower_m': 0.3, 'depth_upper_m': 1.0, 'damage': 0.75, 'scenario': 'high', 'source': 'kok_et_al_2004'}, 
    {'depth_lower_m': 1.0, 'depth_upper_m': 1.5, 'damage': 1.0, 'scenario': 'high', 'source': 'kok_et_al_2004'}, 
    {'depth_lower_m': 1.5, 'depth_upper_m': 2.0, 'damage': 1.0, 'scenario': 'high', 'source': 'kok_et_al_2004'}, 
    {'depth_lower_m': 2.0, 'depth_upper_m': 2.5, 'damage': 1.0, 'scenario': 'high', 'source': 'kok_et_al_2004'}, 
    {'depth_lower_m': 2.5, 'depth_upper_m': 3.0, 'damage': 1.0, 'scenario': 'high', 'source': 'kok_et_al_2004'}, 
    {'depth_lower_m': 3.0, 'depth_upper_m': 4.0, 'damage': 1.0, 'scenario': 'high', 'source': 'kok_et_al_2004'}, 
    {'depth_lower_m': 4.0, 'depth_upper_m': 5.0, 'damage': 1.0, 'scenario': 'high', 'source': 'kok_et_al_2004'}
]


if __name__ == '__main__':

    #countries = get_countries()
    #for idx, country in countries.iterrows():
    #    #if country['iso3'] == 'TJK':
    #    print(country['country'])

    # scenarios = get_scenarios()
    # for scenario in scenarios:
    #     print(scenario)

    tropical_storm_scenarios = get_tropical_storm_scenarios()
    for scenario in tropical_storm_scenarios:
       print(scenario)


