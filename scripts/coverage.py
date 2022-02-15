"""
Script to estimate population coverage.

Written by Ed Oughton.

February 2022.

"""
import os
import configparser
import pandas as pd
import geopandas as gpd

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW = os.path.join(BASE_PATH, 'raw')
DATA_PROCESSED = os.path.join(BASE_PATH, 'processed')


def generate_coverage_polygons(country):
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
    regions = gpd.read_file(path, crs=crs)#[:5]

    technologies = [
        'GSM',
        'UMTS',
        'LTE',
        'NR',
    ]

    for idx, region in regions.iterrows():

        gid_level = 'GID_{}'.format(regional_level)
        gid_id = region[gid_level]

        for technology in technologies:#[:1]:

            filename = '{}_{}.shp'.format(technology, gid_id)
            folder = os.path.join(DATA_PROCESSED, iso3, 'sites', technology)
            path = os.path.join(folder, filename)

            if not os.path.exists(path):
                continue

            sites = gpd.read_file(path, crs=crs)#[:1]
            sites.to_crs(epsg=3857, inplace=True)

            sites['geometry'] = sites['geometry'].buffer(10000)
            geoms = sites.geometry.unary_union
            buffers = gpd.GeoDataFrame(geometry=[geoms], crs=3857)
            buffers = buffers.explode(index_parts=False).reset_index(drop=True)

            m_region = gpd.GeoDataFrame(gpd.GeoSeries(region['geometry']))
            m_region = m_region.rename(columns={0:'geometry'}).set_geometry('geometry')
            m_region = m_region.set_crs(epsg=4326)
            m_region.to_crs(epsg=3857, inplace=True)

            buffers = buffers.overlay(m_region, how='intersection')

            if len(buffers) == 0:
                continue

            filename = '{}_{}.shp'.format(technology, gid_id)
            folder = os.path.join(DATA_PROCESSED, iso3, 'sites', technology, 'buffer')

            if not os.path.exists(folder):
                os.mkdir(folder)

            path_output = os.path.join(folder, filename)
            buffers.to_file(path_output, crs='epsg:3857')

    return


def estimate_coverage(country):
    """
    Estimate population coverage by region.

    """
    iso3 = country['iso3']
    name = country['country']
    regional_level = country['gid_region']

    filename = 'regional_data.csv'
    folder = os.path.join(DATA_PROCESSED, iso3)
    path = os.path.join(folder, filename)
    regional_data = pd.read_csv(path)#[:1]

    technologies = [
        'GSM',
        'UMTS',
        'LTE',
        'NR',
    ]

    output = []

    for idx, item in regional_data.iterrows():

        gid_id = item['GID_id']
        area_km2 = item['area_km2']
        population_total = item['population_total']

        coverage = {}

        for technology in technologies:

            filename = '{}_{}.shp'.format(technology, gid_id)
            folder = os.path.join(DATA_PROCESSED, iso3, 'sites', technology, 'buffer')
            path = os.path.join(folder, filename)

            if not os.path.exists(path):
                continue

            buffer = gpd.read_file(path, crs='epsg:3857')
            covered_area_km2 = round(buffer.area / 1e6).values[0]

            coverage[technology] = round((covered_area_km2 / area_km2)*100)

        output.append({
            'GID_0': item['GID_0'],
            'GID_id': item['GID_id'],
            'GID_level': item['GID_level'],
            'population_total': item['population_total'],
            'population_over_10': item['population_over_10'],
            'area_km2': item['area_km2'],
            'population_km2': item['population_km2'],
            'population_over_10yrs_km2': item['population_over_10yrs_km2'],
            'GSM_perc': coverage['GSM'] if 'GSM' in coverage else 0,
            'UMTS_perc': coverage['UMTS'] if 'UMTS' in coverage else 0,
            'LTE_perc': coverage['LTE'] if 'LTE' in coverage else 0,
            'NR_perc': coverage['NR'] if 'NR' in coverage else 0,
            'GSM_pop': coverage_pop('GSM', coverage, population_total),
            'UMTS_pop': coverage_pop('UMTS', coverage, population_total),
            'LTE_pop': coverage_pop('LTE', coverage, population_total),
            'NR_pop': coverage_pop('NR', coverage, population_total),
        })

    output = pd.DataFrame(output)
    path = os.path.join(DATA_PROCESSED, iso3, 'coverage.csv')
    output.to_csv(path, index=False)

    return


def coverage_pop(technology, coverage, population_total):
    """
    Calculate the population coverage.

    """
    if technology in coverage:
        output = round((population_total * (coverage[technology])/100))
    else:
        output = 0

    return output


if __name__ == '__main__':

    crs = 'epsg:4326'
    os.environ['GDAL_DATA'] = ("C:\\Users\edwar\\Anaconda3\\Library\\share\\gdal")

    filename = "countries.csv"
    path = os.path.join(DATA_RAW, filename)
    countries = pd.read_csv(path, encoding='latin-1')

    for idx, country in countries.iterrows():

        if not country['iso3'] == 'GHA':
            continue

        print('--working on {}'.format(country['iso3']))

        generate_coverage_polygons(country)

        estimate_coverage(country)

    print('finished')
