"""
Process sites data.

Ed Oughton

February 2022

"""
import sys
import os
import configparser
import pandas as pd
import geopandas as gpd
import pyproj
from shapely.ops import transform
from shapely.geometry import shape, Point, mapping, LineString, MultiPolygon
# from tqdm import tqdm
import rasterio

from misc import (process_country_shapes, process_regions, params, technologies,
    get_countries, get_regions, get_scenarios)
from flood_hazards import process_flooding_layers

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__),'..', 'scripts', 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW = os.path.join(BASE_PATH, 'raw')
DATA_PROCESSED = os.path.join(BASE_PATH, 'processed')


def run_site_processing(iso3):
    """
    Meta function for running site processing.

    """
    filename = "countries.csv"
    path = os.path.join(DATA_RAW, filename)

    countries = pd.read_csv(path, encoding='latin-1')
    country = countries[countries.iso3 == iso3]
    country = country.to_dict('records')[0]

    regional_level = int(country['gid_region'])

    print('Working on create_national_sites_csv')
    create_national_sites_csv(country)

    print('Working on process_country_shapes')
    process_country_shapes(iso3)

    print('Working on process_regions')
    process_regions(iso3, regional_level)

    print('Working on create_national_sites_shp')
    create_national_sites_shp(iso3)

    if regional_level > 0:

        print('Working on segment_by_gid_1')
        segment_by_gid_1(iso3, 1)

        print('Working on create_regional_sites_layer')
        create_regional_sites_layer(iso3, 1)

    if regional_level > 1:

        print('Working on segment_by_gid_2')
        segment_by_gid_2(iso3, 2)

        print('Working on create_regional_sites_layer')
        create_regional_sites_layer(iso3, 2)

    print('Getting regions')
    regions = get_regions(country, regional_level)#[:5]

    print('Getting scenarios')
    scenarios = get_scenarios()#[:5]

    print('Working on process_flooding_layers')
    process_flooding_layers(country, scenarios)

    print('Working on query_hazard_layers')
    query_hazard_layers(country, regions, scenarios, regional_level)

    return


def create_national_sites_csv(country):
    """
    Create a national sites csv layer for a selected country.

    """
    iso3 = country['iso3']#.values[0]

    filename = "mobile_codes.csv"
    path = os.path.join(DATA_RAW, filename)

    mobile_codes = pd.read_csv(path)
    mobile_codes = mobile_codes[['iso3', 'mcc']].drop_duplicates()
    all_mobile_codes = mobile_codes[mobile_codes['iso3'] == iso3]
    all_mobile_codes = all_mobile_codes.to_dict('records')

    output = []

    for row in all_mobile_codes:

        mcc = row['mcc']

        filename = '{}.csv'.format(iso3)
        folder = os.path.join(DATA_PROCESSED, iso3, 'sites')
        path_csv = os.path.join(folder, filename)

        ### Produce national sites data layers
        if not os.path.exists(path_csv):

            # print('-site.csv data does not exist')
            # print('-Subsetting site data for {}: {}'.format(iso3, mcc))

            if not os.path.exists(folder):
                os.makedirs(folder)

            filename = "cell_towers.csv"
            path = os.path.join(DATA_RAW, filename)

            chunksize = 10 ** 6
            for idx, chunk in enumerate(pd.read_csv(path, chunksize=chunksize)):

                country_data = chunk.loc[chunk['mcc'] == mcc]#[:1]

                country_data = country_data.to_dict('records')

                output = output + country_data

    if len(output) == 0:
        # print('-{} had no data'.format(iso3))
        return

    output = pd.DataFrame(output)
    output.to_csv(path_csv, index=False)

    return


def segment_by_gid_1(iso3, level):
    """
    Segment sites by gid_1 bounding box.

    """
    gid_id = 'GID_{}'.format(level)

    filename = '{}.csv'.format(iso3)
    folder = os.path.join(DATA_PROCESSED, iso3, 'sites')
    path = os.path.join(folder, filename)
    sites = pd.read_csv(path)#[:100]

    filename = 'regions_{}_{}.shp'.format(level, iso3)
    folder = os.path.join(DATA_PROCESSED, iso3, 'regions')
    path = os.path.join(folder, filename)
    regions = gpd.read_file(path, crs='epsg:4326')#[:1]

    region = regions.iloc[-1]
    gid_id = region['GID_{}'.format(level)]
    filename = '{}.shp'.format(gid_id)
    folder = os.path.join(DATA_PROCESSED, iso3, 'sites', 'gid_1', 'interim')
    path = os.path.join(folder, filename)
    if os.path.exists(path):
        return

    for idx, region in regions.iterrows(): #tqdm(regions.iterrows(), total=regions.shape[0]):

        gid_level = 'GID_{}'.format(level)

        gid_id = region[gid_level]

        filename = '{}.csv'.format(gid_id)
        folder = os.path.join(DATA_PROCESSED, iso3, 'sites', 'gid_1', 'interim')
        if not os.path.exists(folder):
            os.makedirs(folder)
        path = os.path.join(folder, filename)

        if os.path.exists(path):
            continue

        # if idx == 0:
            # print('-Working on GID_{} regional site layer'.format(level))

        xmin, ymin, xmax, ymax = region['geometry'].bounds

        output = []

        for idx, site in sites.iterrows():

            x, y = site['lon'], site['lat']

            if not xmin <= x <= xmax:
                continue

            if not ymin <= y <= ymax:
                continue

            output.append({
                'radio': site['radio'],
                'mcc': site['mcc'],
                'net': site['net'],
                'area': site['area'],
                'cell': site['cell'],
                'unit': site['unit'],
                'lon': site['lon'],
                'lat': site['lat'],
                'range': site['range'],
                'samples': site['samples'],
                'changeable': site['changeable'],
                'created': site['created'],
                'updated': site['updated'],
                'averageSignal': site['averageSignal']
            })

        if len(output) > 0:

            output = pd.DataFrame(output)
            output.to_csv(path, index=False)

        else:
            continue

    return


def segment_by_gid_2(iso3, level):
    """
    Segment sites by gid_2 bounding box.

    """
    gid_id = 'GID_{}'.format(level)

    filename = 'regions_{}_{}.shp'.format(level, iso3)
    folder = os.path.join(DATA_PROCESSED, iso3, 'regions')
    path = os.path.join(folder, filename)
    regions = gpd.read_file(path, crs='epsg:4326')#[:1]

    for idx, region in regions.iterrows(): #tqdm(regions.iterrows(), total=regions.shape[0]):

        gid_level = 'GID_{}'.format(level)
        gid_id = region[gid_level]

        filename = '{}.shp'.format(region['GID_1'])
        folder_out = os.path.join(DATA_PROCESSED, iso3, 'sites', 'gid_2', 'interim')
        if not os.path.exists(folder_out):
            os.makedirs(folder_out)
        path = os.path.join(folder_out, filename)
        if os.path.exists(path):
            return

        filename = '{}.csv'.format(region['GID_1'])
        folder = os.path.join(DATA_PROCESSED, iso3, 'sites', 'gid_2', 'interim')
        path_out = os.path.join(folder, filename)

        if os.path.exists(path_out):
            continue

        # if idx == 0:
            # print('-Working on GID_{} regional site layer'.format(level))

        xmin, ymin, xmax, ymax = region['geometry'].bounds

        filename = '{}.csv'.format(region['GID_1'])
        folder = os.path.join(DATA_PROCESSED, iso3, 'sites', 'gid_1', 'interim')
        path = os.path.join(folder, filename)
        if not os.path.exists(path):
            continue
        sites = pd.read_csv(path)

        output = []

        for idx, site in sites.iterrows():

            x, y = site['lon'], site['lat']

            if not xmin < x < xmax:
                continue

            if not ymin < y < ymax:
                continue

            output.append({
                'radio': site['radio'],
                'mcc': site['mcc'],
                'net': site['net'],
                'area': site['area'],
                'cell': site['cell'],
                'unit': site['unit'],
                'lon': site['lon'],
                'lat': site['lat'],
                'range': site['range'],
                'samples': site['samples'],
                'changeable': site['changeable'],
                'created': site['created'],
                'updated': site['updated'],
                'averageSignal': site['averageSignal']
            })

        if len(output) > 0:

            output = pd.DataFrame(output)

            filename = '{}.csv'.format(gid_id)
            folder = os.path.join(DATA_PROCESSED, iso3, 'sites', 'gid_2', 'interim')
            path_out = os.path.join(folder, filename)
            output.to_csv(path_out, index=False)

        else:
            continue

    return


def create_national_sites_shp(iso3):
    """
    Create a national sites csv layer for a selected country.

    """
    filename = '{}.csv'.format(iso3)
    folder = os.path.join(DATA_PROCESSED, iso3, 'sites')
    path_csv = os.path.join(folder, filename)

    filename = '{}.shp'.format(iso3)
    path_shp = os.path.join(folder, filename)

    if not os.path.exists(path_shp):

        # print('-Writing site shapefile data for {}'.format(iso3))

        country_data = pd.read_csv(path_csv)#[:10]

        output = []

        for idx, row in country_data.iterrows():
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

        output = gpd.GeoDataFrame.from_features(output, crs='epsg:4326')

        output.to_file(path_shp)


def create_regional_sites_layer(iso3, level):
    """
    Create regional site layers.

    """
    project = pyproj.Transformer.from_proj(
        pyproj.Proj('epsg:4326'), # source coordinate system
        pyproj.Proj('epsg:3857')) # destination coordinate system

    filename = 'regions_{}_{}.shp'.format(level, iso3)
    folder = os.path.join(DATA_PROCESSED, iso3, 'regions')
    path = os.path.join(folder, filename)
    regions = gpd.read_file(path, crs='epsg:4326')#[:1]

    for idx, region in regions.iterrows(): #tqdm(regions.iterrows(), total=regions.shape[0]):

        gid_level = 'GID_{}'.format(level)
        gid_id = region[gid_level]

        filename = '{}.csv'.format(gid_id)
        folder = os.path.join(DATA_PROCESSED, iso3, 'sites', gid_level.lower())
        if not os.path.exists(folder):
            os.mkdir(folder)
        path_out = os.path.join(folder, filename)

        if os.path.exists(path_out):
            continue

        # if idx == 0:
            # print('-Working on regional site layer')

        filename = '{}.csv'.format(region[gid_level])
        folder = os.path.join(DATA_PROCESSED, iso3, 'sites', gid_level.lower(), 'interim')
        path = os.path.join(folder, filename)
        if not os.path.exists(path):
            continue
        sites = pd.read_csv(path)

        output = []

        for idx, site in sites.iterrows():

            geom = Point(site['lon'], site['lat'])

            if region['geometry'].intersects(geom):

                geom_4326 = geom

                geom_3857 = transform(project.transform, geom_4326)

                output.append({
                    'radio': site['radio'],
                    'mcc': site['mcc'],
                    'net': site['net'],
                    'area': site['area'],
                    'cell': site['cell'],
                    'gid_level': gid_level,
                    'gid_id': region[gid_level],
                    'cellid4326': '{}_{}'.format(
                        round(geom_4326.coords.xy[0][0],6),
                        round(geom_4326.coords.xy[1][0],6)
                    ),
                    'cellid3857': '{}_{}'.format(
                        round(geom_3857.coords.xy[0][0],6),
                        round(geom_3857.coords.xy[1][0],6)
                    ),
                })

        if len(output) > 0:

            output = pd.DataFrame(output)
            output.to_csv(path_out, index=False)

        else:
            continue

    return


def query_hazard_layers(country, regions, scenarios, regional_level):
    """
    Query each hazard layer and estimate fragility.

    """
    iso3 = country['iso3']
    name = country['country']
    gid_level = 'GID_{}'.format(regional_level) #regional_level

    for scenario in scenarios: #tqdm(scenarios):

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

                    output.append({
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
                    })

            if len(output) == 0:
                return

            if not os.path.exists(folder_out):
                os.makedirs(folder_out)

            output = pd.DataFrame(output)

            output.to_csv(path_output, index=False)

    return


if __name__ == "__main__":

    # import cProfile

    args = sys.argv

    iso3 = args[1]

    run_site_processing(iso3)

    # countries = get_countries()

    # failures = []

    # for idx, country in countries.iterrows():

    #     try:
    #         print('Trying {}'.format(country['iso3']))
    #         run_site_processing(country['iso3'])
    #     except:
    #         print('--Failed on {}'.format(country['iso3']))
    #         failures.append(country['iso3'])

    # print(failures)
