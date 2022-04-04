"""
Miscellaneous model inputs.

"""
import os
import configparser
import glob
import pandas as pd
import geopandas as gpd

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
        'number_of_cells': 2, #Number of cells to check distance to
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

    return countries


def get_regions(country):
    """


    """

    filename = 'regions_{}_{}.shp'.format(
        country['lowest'],
        country['iso3']
    )

    folder = os.path.join(DATA_PROCESSED, country['iso3'], 'regions')

    path = os.path.join(folder, filename)

    regions = gpd.read_file(path, crs='epsg:4326')#[:1]

    return regions


def get_scenarios(country):
    """

    """
    output = []

    hazard_dir = os.path.join(DATA_PROCESSED, country['iso3'], 'hazards')

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

            if 'inuncoast' and 'wtsub' in scenario:
                if '0_perc_50.tif' in scenario:
                    output.append(scenario)
            elif 'inunriver' in scenario: #and 'MIROC-ESM-CHEM'
                output.append(scenario)
            else:
                continue

        if 'historical' in scenario:
            if any(x in scenario for x in return_periods): #specify return periods
                if 'inuncoast_historical_wtsub_hist' in scenario:
                    output.append(scenario)
                elif 'inunriver' in scenario:
                    output.append(scenario)
                else:
                    continue

    return output


if __name__ == '__main__':

    scenarios = get_scenarios({'iso3': 'GHA'})

    for scenario in scenarios:
        print(scenario)
