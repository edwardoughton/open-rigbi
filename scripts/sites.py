"""
Preprocess sites data.

Ed Oughton

February 2022

"""
import os
import configparser
import pandas as pd
import geopandas as gpd
from tqdm import tqdm

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW = os.path.join(BASE_PATH, 'raw')
DATA_PROCESSED = os.path.join(BASE_PATH, 'processed')


def create_national_sites_layer(country):
    """
    Create a national sites layer for a selected country.

    """
    iso3 = country['iso3']
    name = country['country']
    regional_level = country['gid_region']
    mcc = country['mcc']

    # filename = "cell_towers_2022-02-02-T000000.csv"
    # folder = "../../../site_location_data/OpenCellID"
    # path = os.path.join(folder, filename)
    # all_data = pd.read_csv(path)#[:10]

    filename = '{}.csv'.format(iso3)
    folder = os.path.join(DATA_PROCESSED, iso3, 'sites')
    path_csv = os.path.join(folder, filename)

    ### Produce national sites data layers
    if not os.path.exists(path_csv):

        print('site .csv data does not exist')

        if not os.path.exists(folder):
            os.makedirs(folder)

        # country_data = all_data.loc[all_data['mcc'] == mcc]

        # if len(country_data) == 0:
        #     print('{} had no data'.format(name))
        #     continue

        # country_data.to_csv(path_csv, index=False)

    else:

        country_data = pd.read_csv(path_csv)#[:10]

        output = []

        print('Creating national sites shapefile')
        for idx, row in tqdm(country_data.iterrows(), total=country_data.shape[0]):
            output.append({
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [row['lon'],row['lat']]
                },
                'properties': {
                    'radio': row['radio'],
                    'mcc': row['mcc'],
                    'net': row['net'],
                    'area': row['area'],
                    'cell': row['cell'],
                }
            })

        output = gpd.GeoDataFrame.from_features(output, crs=crs)

        filename = '{}.shp'.format(iso3)
        path_shp = os.path.join(folder, filename)
        output.to_file(path_shp)

    return


def create_regional_sites_layer(country):
    """
    Create regional site layers.

    """
    iso3 = country['iso3']
    regional_level = country['gid_region']

    ### Produce national sites data layers
    filename = '{}.shp'.format(iso3)
    folder = os.path.join(DATA_PROCESSED, iso3, 'sites')
    path_shp = os.path.join(folder, filename)
    sites = gpd.read_file(path_shp, crs=crs)
    sites = sites.to_crs(epsg=3857)

    filename = 'regions_{}_{}.shp'.format(regional_level, iso3)
    folder = os.path.join(DATA_PROCESSED, iso3, 'regions')
    path = os.path.join(folder, filename)
    regions = gpd.read_file(path, crs=crs)#[:5]
    regions = regions.to_crs(epsg=3857)

    print('Creating regional sites shapefiles')
    for idx, region in tqdm(regions.iterrows(), total=regions.shape[0]):

        # if not region['GID_2'] == 'GHA.1.12_1':
        #     continue

        output = []

        gid_level = 'GID_{}'.format(regional_level)
        gid_id = region[gid_level]

        for idx, site in sites.iterrows():
            if region['geometry'].intersects(site['geometry']):
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
                        'cell_id': '{}_{}'.format(
                                round(site['geometry'].coords.xy[0][0], 6),
                                round(site['geometry'].coords.xy[1][0], 6)
                        ),
                    }
                })

        if len(output) > 0:

            output = gpd.GeoDataFrame.from_features(output, crs='epsg:3857')
            filename = '{}.shp'.format(gid_id)
            folder = os.path.join(DATA_PROCESSED, iso3, 'sites', 'regional_sites')
            if not os.path.exists(folder):
                os.mkdir(folder)
            path = os.path.join(folder, filename)
            output.to_file(path)

        else:
            continue

    return


def tech_specific_sites(country):
    """
    Break sites into tech-specific shapefiles.

    """
    iso3 = country['iso3']
    regional_level = country['gid_region']

    filename = 'regions_{}_{}.shp'.format(regional_level, iso3)
    folder = os.path.join(DATA_PROCESSED, iso3, 'regions')
    path = os.path.join(folder, filename)
    regions = gpd.read_file(path, crs=crs)#[:5]

    technologies = [
        'GSM',
        'UMTS',
        'LTE',
        'NR',
    ]

    for idx, region in tqdm(regions.iterrows(), total=regions.shape[0]):

        # if not region['GID_2'] == 'GHA.1.12_1':
        #     continue

        gid_level = 'GID_{}'.format(regional_level)
        gid_id = region[gid_level]

        filename = '{}.shp'.format(gid_id)
        folder = os.path.join(DATA_PROCESSED, iso3, 'sites', 'regional_sites')
        path = os.path.join(folder, filename)
        if not os.path.exists(path):
            continue
        sites = gpd.read_file(path, crs='epsg:3857')

        for technology in technologies:

            output = []

            for idx, site in sites.iterrows():
                if technology == site['radio']:
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
                            'cell_id': '{}_{}'.format(
                                round(site['geometry'].coords.xy[0][0], 6),
                                round(site['geometry'].coords.xy[1][0], 6)
                            ),
                        }
                    })

            if len(output) > 0:

                output = gpd.GeoDataFrame.from_features(output, crs='epsg:3857')
                filename = '{}_{}.shp'.format(technology, gid_id)
                folder = os.path.join(DATA_PROCESSED, iso3, 'sites', technology)
                if not os.path.exists(folder):
                    os.mkdir(folder)
                path = os.path.join(folder, filename)
                output.to_file(path)

            else:
                continue

    return


if __name__ == "__main__":

    crs = 'epsg:4326'

    filename = "countries.csv"
    path = os.path.join(DATA_RAW, filename)
    countries = pd.read_csv(path, encoding='latin-1')

    filename = "mobile_codes.csv"
    path = os.path.join(DATA_RAW, filename)
    mobile_codes = pd.read_csv(path)
    mobile_codes = mobile_codes[['iso2', 'mcc']].drop_duplicates()
    mobile_codes['iso2'] = mobile_codes['iso2'].str.upper()
    countries = pd.merge(countries, mobile_codes, left_on = 'iso2', right_on = 'iso2')

    for idx, country in countries.iterrows():

        if not country['iso3'] == 'GHA':
            continue

        print('--Working on {}'.format(country['country']))

        # create_national_sites_layer(country)

        create_regional_sites_layer(country)

        tech_specific_sites(country)

    print('--Complete')
