"""
Process GDP data.

"""
import os
import configparser
# import json
# import csv
import geopandas as gpd
import pandas as pd
# import glob
# import pyproj
# from shapely.geometry import MultiPolygon, mapping, MultiLineString
# from shapely.ops import transform, unary_union, nearest_points
# import rasterio
# from rasterio.mask import mask
# from rasterstats import zonal_stats
# from tqdm import tqdm

from misc import get_countries

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW = os.path.join(BASE_PATH, 'raw')
DATA_PROCESSED = os.path.join(BASE_PATH, 'processed')


def load_murakami_gdp_data(country):
    """
    Load Murakami & Yamagata (2019) gdp data.

    """
    filename = 'gdp_ssp1.csv'
    folder = os.path.join(DATA_PROCESSED, country['iso3'], 'gridded_gdp')
    if not os.path.exists(folder):
        os.mkdir(folder)
    path = os.path.join(folder, filename)

    if not os.path.exists(path):
        filename = 'gdp_ssp1.csv'
        folder_in = os.path.join(DATA_RAW, 'gridded_gdp')
        path_in = os.path.join(folder_in, filename)
        data_csv = pd.read_csv(path_in)
        data_csv = data_csv[['px','py','ISO3', 'g1_2020']]
        data_csv = data_csv[data_csv.ISO3 == country['iso3']]
        data_csv.to_csv(path, index=False)
    else:
        data_csv = pd.read_csv(path)

    filename = 'grid.shp'
    folder = os.path.join(DATA_PROCESSED, country['iso3'], 'gridded_gdp')
    if not os.path.exists(folder):
        os.mkdir(folder)
    path = os.path.join(folder, filename)

    if not os.path.exists(path):
        filename = 'grid.shp'
        folder_in = os.path.join(DATA_RAW, 'gridded_gdp', 'grid')
        path_in = os.path.join(folder_in, filename)
        data_shp = gpd.read_file(path_in, crs='epsg:4326')#[:20]
        data_shp = data_shp[data_shp.ISO3 == country['iso3']]
        data_shp.to_file(path, crs='epsg:4326')
    else:
        data_shp = gpd.read_file(path, crs='epsg:4326')

    output = []

    for idx, datum_shp in data_shp.iterrows():

        lon_lat_shp = '{}_{}'.format(
            round(datum_shp['px'],3),
            round(datum_shp['py'], 3),
        )

        for idx, datum_csv in data_csv.iterrows():

            lon_lat_csv = '{}_{}'.format(
                round(datum_csv['px'], 3),
                round(datum_csv['py'], 3),
            )

            if lon_lat_csv == lon_lat_shp:

                output.append({
                    'type': 'Polygon',
                    'geometry': datum_shp['geometry'],
                    'properties': {
                        'g1_2020': round(datum_csv['g1_2020'] * 1e3),
                        'px': datum_csv['px'],
                        'py': datum_csv['py'],
                    }
                })

    if len(output) > 0:

        output = gpd.GeoDataFrame.from_features(output, crs='epsg:4326')

        filename = 'gdp_grid.shp'
        folder = os.path.join(DATA_PROCESSED, country['iso3'], 'gridded_gdp')
        path = os.path.join(folder, filename)
        output.to_file(path, crs='epsg:4326')

    return


def load_kummu_gdp_data():
    """
    Load Kummu et al. gdp data.

    https://www.nature.com/articles/sdata20184

    """
    filename = 'GDP_PPP_1990_2015_5arcmin_v2.nc'
    folder = os.path.join(DATA_RAW, 'gridded_gdp','doi_10.5061_dryad.dk1j0__v2')
    path = os.path.join(folder, filename)
    data = Dataset(path,'r')

    # for i in data.variables:
    #     print(i)

    # lon = data.variables['longitude'][:] #4 - 11
    # lat = data.variables['latitude'][:] #-4 - 1

    # coords = {}

    # for idx_lon, i_lon in enumerate(lon):
    #     for idx_lat, i_lat in enumerate(lat):
    #         if 6 < i_lon < 6.2:
    #             if 0 < i_lat < .2:
    #                 key = "{}_{}".format(idx_lon, idx_lat)
    #                 value = "{}_{}".format(i_lon, i_lat)
    #                 coords[key] = value
    # ###2232_1078
    # print(coords)

    time = data.variables['time'][:]
    most_recent_year = time[len(time)-1] ##(last position of list)

    gdp = data.variables['GDP_PPP']#[:]
    most_recent_gdp = gdp[len(gdp)-1] ##(last position of list)
    # print(len(most_recent_gdp))
    for idx, i in enumerate(most_recent_gdp):
        if idx == 2232:
            print(i)

    # print(gdp)

    # print(data.groups)

    return



if __name__ == "__main__":

    countries = get_countries()

    for idx, country in countries.iterrows():

        if not country['iso3'] == 'GHA':
            continue

        load_murakami_gdp_data(country)

        # load_kummu_gdp_data()
