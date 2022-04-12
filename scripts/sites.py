"""
Preprocess sites data.

Ed Oughton

February 2022

"""
import os
import configparser
import pandas as pd
import geopandas as gpd
import pyproj
from shapely.ops import transform
from shapely.geometry import shape, Point, mapping, LineString, MultiPolygon

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
    mcc = country['mcc']

    filename = '{}.csv'.format(iso3)
    folder = os.path.join(DATA_PROCESSED, iso3, 'sites')
    path_csv = os.path.join(folder, filename)

    ### Produce national sites data layers
    if not os.path.exists(path_csv):

        print('site .csv data does not exist')

        if not os.path.exists(folder):
            os.makedirs(folder)

        filename = "cell_towers.csv"
        path = os.path.join(DATA_RAW, filename)
        all_data = pd.read_csv(path)#[:10]

        country_data = all_data.loc[all_data['mcc'] == mcc]

        if len(country_data) == 0:
            print('{} had no data'.format(name))
            return

        country_data.to_csv(path_csv, index=False)

    else:

        country_data = pd.read_csv(path_csv)#[:10]

        output = []

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


def process_country_shapes(country):
    """
    Creates a single national boundary for the desired country.

    Parameters
    ----------
    country : dict
        Contains all desired country information.

    """
    iso3 = country['iso3']

    path = os.path.join(DATA_PROCESSED, iso3)

    # if os.path.exists(os.path.join(path, 'national_outline.shp')):
    #     return 'Completed national outline processing'

    if not os.path.exists(path):
        os.makedirs(path)

    shape_path = os.path.join(path, 'national_outline.shp')

    path = os.path.join(DATA_RAW, 'gadm36_levels_shp', 'gadm36_0.shp')
    countries = gpd.read_file(path)

    single_country = countries[countries.GID_0 == iso3].reset_index()

    # # if not iso3 == 'MDV':
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


def process_regions(country):
    """
    Function for processing the lowest desired subnational
    regions for the chosen country.

    Parameters
    ----------
    country : dict
        Contains all desired country information.

    """
    regions = []

    iso3 = country['iso3']
    level = country['lowest']

    for regional_level in range(1, level + 1):

        filename = 'regions_{}_{}.shp'.format(regional_level, iso3)
        folder = os.path.join(DATA_PROCESSED, iso3, 'regions')
        path_processed = os.path.join(folder, filename)

        # if os.path.exists(path_processed):
        #     continue

        if not os.path.exists(folder):
            os.mkdir(folder)

        filename = 'gadm36_{}.shp'.format(regional_level)
        path_regions = os.path.join(DATA_RAW, 'gadm36_levels_shp', filename)
        regions = gpd.read_file(path_regions)

        regions = regions[regions.GID_0 == iso3]

        regions['geometry'] = regions.apply(remove_small_shapes, axis=1)

        try:
             regions.to_file(path_processed, driver='ESRI Shapefile')
        except:
            print('Unable to write {}'.format(filename))
            pass

    return


def create_regional_sites_layer(country):
    """
    Create regional site layers.

    """
    iso3 = country['iso3']
    regional_level = country['gid_region']

    project = pyproj.Transformer.from_proj(
        pyproj.Proj('epsg:4326'), # source coordinate system
        pyproj.Proj('epsg:3857')) # destination coordinate system

    ### Produce national sites data layers
    filename = '{}.shp'.format(iso3)
    folder = os.path.join(DATA_PROCESSED, iso3, 'sites')
    path_shp = os.path.join(folder, filename)
    sites = gpd.read_file(path_shp, crs='epsg:4326')
    # sites = sites.to_crs(epsg=3857)

    filename = 'regions_{}_{}.shp'.format(regional_level, iso3)
    folder = os.path.join(DATA_PROCESSED, iso3, 'regions')
    path = os.path.join(folder, filename)
    regions = gpd.read_file(path, crs='epsg:4326')#[:5]
    # regions = regions.to_crs(epsg=3857)

    for idx, region in tqdm(regions.iterrows(), total=regions.shape[0]):

        if not region['GID_2'] == 'GHA.1.12_1':
            continue

        output = []

        gid_level = 'GID_{}'.format(regional_level)
        gid_id = region[gid_level]

        for idx, site in sites.iterrows():
            if region['geometry'].intersects(site['geometry']):

                geom_4326 = site['geometry']

                # apply projection
                geom_3857 = transform(project.transform, geom_4326)

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
                        'cell_id_4326': '{}_{}'.format(
                            round(geom_4326.coords.xy[0][0],6),
                            round(geom_4326.coords.xy[1][0],6)
                        ),
                        'cell_id_3857': '{}_{}'.format(
                            round(geom_3857.coords.xy[0][0],6),
                            round(geom_3857.coords.xy[1][0],6)
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

        ### Separate out site data to .csv
        create_national_sites_layer(country)

        ### Write to shapefiles
        create_national_sites_layer(country)

        ### Process country shapes
        process_country_shapes(country)

        ### Process region shapes
        process_regions(country)

        ### Create regional site layer
        create_regional_sites_layer(country)

        ### Create technology specific site layer
        tech_specific_sites(country)

    print('--Complete')
