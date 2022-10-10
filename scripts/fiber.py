"""
Process fiber.

"""
import os
import configparser
import pandas as pd
import geopandas as gpd
from shapely.geometry import mapping, MultiLineString
import fiona

from misc import get_countries

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW = os.path.join(BASE_PATH, 'raw')
DATA_PROCESSED = os.path.join(BASE_PATH, 'processed')


def process_existing_fiber(country):
    """
    Load and process existing fiber data.

    """
    iso3 = country['iso3']
    iso2 = country['iso2'].lower()

    folder = os.path.join(DATA_PROCESSED, iso3, 'network_existing')
    if not os.path.exists(folder):
        os.makedirs(folder)
    filename = 'core_edges_existing.shp'
    path_output = os.path.join(folder, filename)

    # if os.path.exists(path_output):
    #     return print('Existing fiber already processed')

    path = os.path.join(DATA_RAW, 'afterfiber', 'afterfiber.shp')

    shapes = fiona.open(path)

    data = []

    for item in shapes:
        if item['properties']['iso2'] == iso2:
            if item['geometry']['type'] == 'LineString':
                if int(item['properties']['live']) == 1:
                    data.append({
                        'type': 'Feature',
                        'geometry': {
                            'type': 'LineString',
                            'coordinates': item['geometry']['coordinates'],
                        },
                        'properties': {
                            'operators': item['properties']['operator'],
                            'source': 'existing'
                        }
                    })

            if item['geometry']['type'] == 'MultiLineString':
                if int(item['properties']['live']) == 1:

                    for line in list(MultiLineString(item['geometry']['coordinates']).geoms):
                        data.append({
                            'type': 'Feature',
                            'geometry': mapping(line),
                            'properties': {
                                'operators': item['properties']['operator'],
                                'source': 'existing'
                            }
                        })

    if len(data) == 0:
        return print('No existing infrastructure')

    data = gpd.GeoDataFrame.from_features(data)
    data.to_file(path_output, crs='epsg:4326')

    return


if __name__ == '__main__':

    countries = get_countries()

    for idx, country in countries.iterrows():

        if not country['iso3'] in ['MWI']: #'GHA',
            continue

        process_existing_fiber(country)
