"""
Preprocess sites data.

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
from tqdm import tqdm

from misc import process_country_shapes, process_regions

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
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

    print('Working on create_national_sites_csv')
    create_national_sites_csv(country)

    print('Working on process_country_shapes')
    process_country_shapes(iso3)

    print('Working on process_regions')
    process_regions(iso3, 1)

    print('Working on create_national_sites_shp')
    create_national_sites_shp(iso3)

    print('Working on segment_by_gid_1')
    segment_by_gid_1(iso3, 1)

    print('Working on create_regional_sites_layer')
    create_regional_sites_layer(iso3, 1)

    # if level >= 2:

    #     segment_by_gid_2(iso3, 2)

    #     create_regional_sites_layer(iso3, 2)

    # tech_specific_sites_gid_1(iso3, level)

    # if str(level) == "2":
    #
    #     tech_specific_sites_gid_2(iso3, level)

    return


def create_national_sites_csv(country):
    """
    Create a national sites csv layer for a selected country.

    """
    iso3 = country['iso3'].values[0]

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

            print('-site.csv data does not exist')
            print('-Subsetting site data for {}: {}'.format(iso3, mcc))

            if not os.path.exists(folder):
                os.makedirs(folder)

            filename = "cell_towers.csv"
            path = os.path.join(DATA_RAW, filename)

            chunksize = 10 ** 6
            for idx, chunk in enumerate(pd.read_csv(path, chunksize=chunksize)):

                country_data = chunk.loc[chunk['mcc'] == mcc]

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
    sites = pd.read_csv(path)[:100]

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

    for idx, region in tqdm(regions.iterrows(), total=regions.shape[0]):

        gid_level = 'GID_{}'.format(level)

        gid_id = region[gid_level]

        filename = '{}.csv'.format(gid_id)
        folder = os.path.join(DATA_PROCESSED, iso3, 'sites', 'gid_1', 'interim')
        if not os.path.exists(folder):
            os.makedirs(folder)
        path = os.path.join(folder, filename)

        if os.path.exists(path):
            continue

        if idx == 0:
            print('-Working on GID_{} regional site layer'.format(level))

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

    for idx, region in tqdm(regions.iterrows(), total=regions.shape[0]):

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

        if idx == 0:
            print('-Working on GID_{} regional site layer'.format(level))

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

        print('-Writing site shapefile data for {}'.format(iso3))

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
    regions = gpd.read_file(path, crs='epsg:4326')#[:2]

    for idx, region in tqdm(regions.iterrows(), total=regions.shape[0]):

        gid_level = 'GID_{}'.format(level)
        gid_id = region[gid_level]

        filename = '{}.csv'.format(gid_id)
        folder = os.path.join(DATA_PROCESSED, iso3, 'sites', gid_level.lower())
        if not os.path.exists(folder):
            os.mkdir(folder)
        path_out = os.path.join(folder, filename)

        if os.path.exists(path_out):
            continue

        if idx == 0:
            print('-Working on regional site layer')

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

                # apply projection
                geom_3857 = transform(project.transform, geom_4326)

                output.append({
                #     'type': 'Feature',
                #     'geometry': geom,
                #     'properties': {
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
                    # }
                })

        if len(output) > 0:

            output = pd.DataFrame(output)
            output.to_csv(path_out, index=False)

        else:
            continue

    return


def tech_specific_sites_gid_1(iso3, level):
    """
    Break sites into tech-specific shapefiles.

    """
    project = pyproj.Transformer.from_proj(
        pyproj.Proj('epsg:4326'), # source coordinate system
        pyproj.Proj('epsg:3857')) # destination coordinate system

    filename = 'regions_{}_{}.shp'.format(level, iso3)
    folder = os.path.join(DATA_PROCESSED, iso3, 'regions')
    path = os.path.join(folder, filename)
    regions = gpd.read_file(path, crs='epsg:4326')#[:5]

    region = regions.iloc[-1]
    gid_id = region['GID_{}'.format(level)]
    folder = os.path.join(DATA_PROCESSED, iso3, 'sites', 'GSM')
    path = os.path.join(folder, 'GSM_{}.shp'.format(gid_id))

    if os.path.exists(path):
        return

    technologies = [
        'GSM',
        'UMTS',
        'LTE',
        'NR',
    ]

    for idx, region in regions.iterrows(): #tqdm(regions.iterrows(), total=regions.shape[0]):

        # if not region['GID_2'] == 'GHA.1.12_1':
        #     continue

        gid_level = 'GID_{}'.format(level)
        gid_id = region[gid_level]

        filename = '{}.shp'.format(gid_id)
        folder = os.path.join(DATA_PROCESSED, iso3, 'sites', 'regional_sites')
        path = os.path.join(folder, filename)
        if not os.path.exists(path):
            continue
        sites = gpd.read_file(path, crs='epsg:4326')

        for technology in technologies:

            filename = '{}_{}.shp'.format(technology, gid_id)
            folder = os.path.join(DATA_PROCESSED, iso3, 'sites', technology)
            if not os.path.exists(folder):
                os.mkdir(folder)
            path = os.path.join(folder, filename)

            if os.path.exists(path):
                continue

            if technology == 'GSM' and idx == 0:
                print('-Creating technology specific site layers')

            output = []

            for idx, site in sites.iterrows():
                if technology == site['radio']:

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
                            'cellid4326': '{}_{}'.format(
                                round(geom_4326.coords.xy[0][0],6),
                                round(geom_4326.coords.xy[1][0],6)
                            ),
                            'cellid3857': '{}_{}'.format(
                                round(geom_3857.coords.xy[0][0],6),
                                round(geom_3857.coords.xy[1][0],6)
                            ),
                        }
                    })

            if len(output) > 0:

                output = gpd.GeoDataFrame.from_features(output, crs='epsg:4326')
                output.to_file(path)

            else:
                continue

    return


def create_regional_sites_layer_gid_2(iso3, level):
    """
    Create regional site layers.

    """
    gid_id = 'GID_{}'.format(level)

    project = pyproj.Transformer.from_proj(
        pyproj.Proj('epsg:4326'), # source coordinate system
        pyproj.Proj('epsg:3857')) # destination coordinate system

    filename = 'regions_{}_{}.shp'.format(level, iso3)
    folder = os.path.join(DATA_PROCESSED, iso3, 'regions')
    path = os.path.join(folder, filename)
    regions = gpd.read_file(path, crs='epsg:4326')#[:1]
    # regions = regions.to_crs(epsg=3857)

    ##Check if complete processing has been carried out yet
    region = regions.iloc[-1]
    gid_id = region['GID_{}'.format(level)]
    filename = '{}.shp'.format(gid_id)
    folder = os.path.join(DATA_PROCESSED, iso3, 'sites', 'regional_sites')
    path = os.path.join(folder, filename)
    if os.path.exists(path):
        return

    for idx, region in regions.iterrows(): #tqdm(regions.iterrows(), total=regions.shape[0]):

        gid_level = 'GID_{}'.format(level)
        gid_2 = region[gid_level]
        gid_1_num = gid_2.split('.')[1]
        gid_1 = "{}.{}_1".format(iso3, gid_1_num)

        # if not gid_1 == 'AFG.14_1':
        #     continue

        filename = '{}.shp'.format(gid_2)
        folder = os.path.join(DATA_PROCESSED, iso3, 'sites', 'regional_sites')
        if not os.path.exists(folder):
            os.mkdir(folder)
        path_out = os.path.join(folder, filename)

        # if os.path.exists(path_out):
        #     continue

        filename = '{}.shp'.format(gid_1)
        folder = os.path.join(DATA_PROCESSED, iso3, 'sites', 'regional_sites')
        if not os.path.exists(folder):
            os.mkdir(folder)
        path = os.path.join(folder, filename)
        sites = gpd.read_file(path, crs='epsg:4326')

        if idx == 0:
            print('-Working on regional site layer')

        output = []

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
                        'cellid4326': '{}_{}'.format(
                            round(geom_4326.coords.xy[0][0],6),
                            round(geom_4326.coords.xy[1][0],6)
                        ),
                        'cellid3857': '{}_{}'.format(
                            round(geom_3857.coords.xy[0][0],6),
                            round(geom_3857.coords.xy[1][0],6)
                        ),
                    }
                })

        if len(output) > 0:

            output = gpd.GeoDataFrame.from_features(output, crs='epsg:4326')
            output.to_file(path_out)

        else:
            continue

    return


def tech_specific_sites_gid_2(iso3, level):
    """
    Break sites into tech-specific shapefiles.

    """
    project = pyproj.Transformer.from_proj(
        pyproj.Proj('epsg:4326'), # source coordinate system
        pyproj.Proj('epsg:3857')) # destination coordinate system

    filename = 'regions_{}_{}.shp'.format(level, iso3)
    folder = os.path.join(DATA_PROCESSED, iso3, 'regions')
    path = os.path.join(folder, filename)
    regions = gpd.read_file(path, crs='epsg:4326')#[:5]

    region = regions.iloc[-1]
    gid_id = region['GID_{}'.format(level)]
    folder = os.path.join(DATA_PROCESSED, iso3, 'sites', 'GSM')
    path = os.path.join(folder, 'GSM_{}.shp'.format(gid_id))

    # if os.path.exists(path):
    #     return

    technologies = [
        'GSM',
        'UMTS',
        'LTE',
        'NR',
    ]

    for idx, region in regions.iterrows(): #tqdm(regions.iterrows(), total=regions.shape[0]):

        # if not region['GID_2'] == 'GHA.1.12_1':
        #     continue

        gid_level = 'GID_{}'.format(level)
        gid_2 = region[gid_level]
        gid_1_num = gid_2.split('.')[1]
        gid_1 = "{}.{}_1".format(iso3, gid_1_num)

        # if not gid_1 == 'AFG.14_1':
        #     continue

        for technology in technologies:

            filename = '{}_{}.shp'.format(technology, gid_2)
            folder = os.path.join(DATA_PROCESSED, iso3, 'sites', technology)
            if not os.path.exists(folder):
                os.mkdir(folder)
            path_out = os.path.join(folder, filename)

            # if os.path.exists(path):
            #     continue

            filename = '{}_{}.shp'.format(technology, gid_1)
            folder = os.path.join(DATA_PROCESSED, iso3, 'sites', technology)
            if not os.path.exists(folder):
                os.mkdir(folder)
            path = os.path.join(folder, filename)
            if not os.path.exists(path):
                continue
            sites = gpd.read_file(path, crs="epsg:4326")

            if technology == 'GSM' and idx == 0:
                print('-Creating technology specific site layers')

            output = []

            for idx, site in sites.iterrows():
                if technology == site['radio']:

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
                            'cellid4326': '{}_{}'.format(
                                round(geom_4326.coords.xy[0][0],6),
                                round(geom_4326.coords.xy[1][0],6)
                            ),
                            'cellid3857': '{}_{}'.format(
                                round(geom_3857.coords.xy[0][0],6),
                                round(geom_3857.coords.xy[1][0],6)
                            ),
                        }
                    })

            if len(output) > 0:

                output = gpd.GeoDataFrame.from_features(output, crs='epsg:4326')
                output.to_file(path_out)

            else:
                continue

    return


def extract_oci_site_info(country):
    """
    Extract site info on unique cells and sites.

    """
    if country['iso3'] in ['GUM']:
        return

    filename = 'unique_cells.csv'
    folder = os.path.join(DATA_PROCESSED, country['iso3'], 'sites')
    path_out = os.path.join(folder, filename)

    if os.path.exists(path_out):
        return

    print('-Working on {}: {}'.format(country['iso3'], country['country']))

    output = []

    unique_entries = set()

    filename = "{}.csv".format(country['iso3'])
    folder = os.path.join(DATA_PROCESSED, country['iso3'], 'sites')
    path = os.path.join(folder, filename)
    if not os.path.exists(path):
        return
    sites = pd.read_csv(path)

    for idx, site in sites.iterrows():

        handle = "{}_{}_{}".format(
            site['radio'],
            site['net'],
            site['cell'],
        )
        unique_entries.add(handle)

    radios = sites['radio'].unique()
    nets = sites['net'].unique()

    for radio in list(radios):
        for net in list(nets):

            cells = 0

            for item in list(unique_entries):
                if item.split("_")[0] == radio:
                    if str(item.split("_")[1]) == str(net):
                        cells += 1

            output.append({
                'iso3': country['iso3'],
                'iso2': country['iso2'],
                'country': country['country'],
                'radio': radio,
                'mcc': country['mcc'],
                'net': net,
                'cells': cells
            })

    if len(output) == 0:
        return

    output = pd.DataFrame(output)
    output.to_csv(path_out, index=False)

    return


def collect_site_info(countries):
    """

    """
    output = []

    for idx, country in countries.iterrows():

        # if not country['iso3'] == 'AFG':
        #     continue

        filename = 'unique_cells.csv'
        folder = os.path.join(DATA_PROCESSED, country['iso3'], 'sites')
        path = os.path.join(folder, filename)
        if not os.path.exists(path):
            continue
        site_info = pd.read_csv(path)

        for idx, info in site_info.iterrows():

            output.append({
                'iso3': info['iso3'],
                'iso2': info['iso2'],
                'country': info['country'],
                'radio': info['radio'],
                'mcc': info['mcc'],
                'net': info['net'],
                'cells': info['cells'],
            })

    if len(output) == 0:
        return

    output = pd.DataFrame(output)
    filename = 'globally_unique_cells.csv'
    path_out = os.path.join(DATA_PROCESSED, filename)
    output.to_csv(path_out, index=False)

    return


def collect_regional_site_info(countries):
    """

    """
    for idx, country in countries.iterrows():

        # if not country['iso3'] == 'AFG':
        #     continue

        folder = os.path.join(DATA_PROCESSED, country['iso3'], 'regions')
        filename = "regions_{}_{}.shp".format(country['gid_region'], country['iso3'])
        path = os.path.join(folder, filename)
        if not os.path.exists(path):
            continue
        regions = gpd.read_file(path)

        directory = os.path.join(DATA_PROCESSED, country['iso3'], 'sites', 'regional_sites')

        output = []

        for idx, region in regions.iterrows():

            gid_level = "GID_{}".format(country['gid_region'])
            gid_id = region[gid_level]

            path = os.path.join(directory, gid_id + '.shp')
            if os.path.exists(path):
                sites = gpd.read_file(path)

                for idx, site in sites.iterrows():

                    output.append({
                        'radio': site['radio'],
                        'mcc': site['mcc'],
                        'net': site['net'],
                        'area': site['area'],
                        'cell': site['cell'],
                        'gid_level': site['gid_level'],
                        'gid_id': site['gid_id'],
                        # 'iso3': site['iso3'],
                        # 'iso2': site['iso2'],
                        # 'country': info['country'],
                    })
            else:
                continue

        if len(output) == 0:
            return

        output = pd.DataFrame(output)
        filename = 'cells_by_region.csv'
        path_out = os.path.join(DATA_PROCESSED, country['iso3'], 'sites', filename)
        output.to_csv(path_out, index=False)

    return


if __name__ == "__main__":

    args = sys.argv

    iso3 = args[1]
    # print(len(iso3))
    print('Running site processing for {}'.format(iso3))
    # run_site_processing(iso3)
