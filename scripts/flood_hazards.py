"""
Preprocess sites data.

Ed Oughton

February 2022

"""
import os
import json
import configparser
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.mask import mask
import glob

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW = os.path.join(BASE_PATH, 'raw')
DATA_PROCESSED = os.path.join(BASE_PATH, 'processed')

filename = "countries.csv"
path = os.path.join(DATA_RAW, filename)
countries = pd.read_csv(path, encoding='latin-1')


def process_hazard_layer(country, path_in, path_out):
    """
    Clip the hazard layer to the chosen country boundary
    and place in desired country folder.

    Parameters
    ----------
    country : dict
        Contains all desired country information.
    path_in : string
        The path for the chosen global hazard file to be processed.
    path_out : string
        The path to write the clipped hazard file.

    """
    iso3 = country['iso3']
    regional_level = country['gid_region']

    hazard = rasterio.open(path_in, 'r+')
    hazard.nodata = 255
    hazard.crs.from_epsg(4326)

    iso3 = country['iso3']
    path_country = os.path.join(DATA_PROCESSED, iso3,
        'national_outline.shp')

    if os.path.exists(path_country):
        country = gpd.read_file(path_country)
    else:
        print('Must generate national_outline.shp first' )

    if os.path.exists(path_out):
        return

    bbox = country.envelope
    geo = gpd.GeoDataFrame()

    geo = gpd.GeoDataFrame({'geometry': bbox})

    coords = [json.loads(geo.to_json())['features'][0]['geometry']]

    out_img, out_transform = mask(hazard, coords, crop=True)

    out_meta = hazard.meta.copy()

    out_meta.update({"driver": "GTiff",
                    "height": out_img.shape[1],
                    "width": out_img.shape[2],
                    "transform": out_transform,
                    "crs": 'epsg:4326'})

    with rasterio.open(path_out, "w", **out_meta) as dest:
            dest.write(out_img)

    return


if __name__ == "__main__":

    os.environ['GDAL_DATA'] = ("C:\\Users\\edwar\\Anaconda3\\Library\\share\\gdal")

    failures = []

    for idx, country in countries.iterrows():

        iso3 = country['iso3']
        name = country['country']

        if not iso3 == 'GHA':
            continue

        hazard_dir = os.path.join(DATA_RAW, 'hazard_scenarios')
        paths = glob.glob(os.path.join(hazard_dir, "*.tif"))#[:5]

        for path_in in paths:

            filename = os.path.basename(path_in)
            folder = os.path.join(DATA_PROCESSED, iso3, 'hazards')
            path_out = os.path.join(folder, filename)

            if not os.path.exists(path_out):

                print('--{}: {}'.format(name, filename))

                if not os.path.exists(folder):
                    os.makedirs(folder)

                try:
                    outcome = process_hazard_layer(country, path_in, path_out)
                except:
                    failures.append({
                        'iso3': iso3,
                        'filename': filename
                    })

    print(failures)
