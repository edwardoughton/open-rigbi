"""
Preprocesses by the flooding hazard and surface water layers.

This involves clipping the global mosaic to each country geometry,
and exporting as a .tiff file to the data/processed folder.

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
from shapely.geometry import box

from misc import get_countries, get_scenarios

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW = os.path.join(BASE_PATH, 'raw')
DATA_PROCESSED = os.path.join(BASE_PATH, 'processed')


def process_flooding_layers(country, scenarios):
    """
    Loop to process all flood layers.

    """

    iso3 = country['iso3']
    name = country['country']

    hazard_dir = os.path.join(DATA_RAW, 'flood_hazard')
    # paths = glob.glob(os.path.join(hazard_dir, "*.tif"))#[:5]

    for scenario in scenarios:

        filename = os.path.basename(scenario)
        path_in = os.path.join(hazard_dir, filename)

        folder = os.path.join(DATA_PROCESSED, iso3, 'hazards', 'flooding')
        if not os.path.exists(folder):
            os.makedirs(folder)
        path_out = os.path.join(folder, filename)

        if not os.path.exists(path_out):

            print('--{}: {}'.format(name, filename))

            if not os.path.exists(folder):
                os.makedirs(folder)

            # try:
            process_flood_layer(country, path_in, path_out)
            # except:
            #     failures.append({
            #         'iso3': iso3,
            #         'filename': filename
            #     })

    return


def process_flood_layer(country, path_in, path_out):
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

    hazard = rasterio.open(path_in, 'r+', BIGTIFF='YES')
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

    geo = gpd.GeoDataFrame()

    geo = gpd.GeoDataFrame({'geometry': country['geometry']})

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


def process_surface_water_layers(country):
    """
    Loop to process all water mask layers.
    """
    folder = os.path.join(DATA_RAW, 'global_surface_water')
    paths = glob.glob(os.path.join(folder, "*.tif"))#[:5]

    failures = []

    for path_in in paths:

        filename = os.path.basename(path_in)
        folder = os.path.join(DATA_PROCESSED, country['iso3'], 'surface_water')
        path_out = os.path.join(folder, filename)

        if not os.path.exists(path_out):

            if not os.path.exists(folder):
                os.makedirs(folder)

            try:
                process_water_layer(country, path_in, path_out)
            except:
                failures.append({
                    'iso3': country['iso3'],
                    'filename': filename
                })

    stitch_layers(country)

    return failures


def process_water_layer(country, path_in, path_out):
    """
    Clip the water layer to the chosen country boundary
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

    geo = gpd.GeoDataFrame()

    geo = gpd.GeoDataFrame({'geometry': country['geometry']}, index=[0])

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


def stitch_layers(country):
    """

    """
    folder = os.path.join(DATA_PROCESSED, country['iso3'], 'surface_water')
    path_out = os.path.join(folder, 'surface_water.tif')

    folder = os.path.join(DATA_PROCESSED, country['iso3'], 'surface_water')
    paths = glob.glob(os.path.join(folder, "*.tif"))#[:5]

    data = []
    import rasterio.merge
    for path in paths:
        interim = rasterio.open(path)
        data.append(interim)

    bounds=None
    res=None
    nodata=None
    precision=7

    def merge(input1, bounds, res, nodata, precision):
        import warnings
        warnings.warn("Deprecated; Use rasterio.merge instead", DeprecationWarning)
        return rasterio.merge.merge(input1, bounds, res, nodata)
# bounds=None, res=None, nodata=None, dtype=None, precision=None
    # dataset1 = rasterio.open("raster1.tif")
    # dataset2 = rasterio.open("raster2.tif")

    dest, output_transform=merge(data, bounds, res, nodata, precision)
    with rasterio.open(path) as src:
            out_meta = src.meta.copy()
    out_meta.update({"driver": "GTiff",
                    "height": dest.shape[1],
                    "width": dest.shape[2],
                    "transform": output_transform})
    with rasterio.open(path_out, "w", **out_meta) as dest1:
            dest1.write(dest)

    return



if __name__ == "__main__":

    os.environ['GDAL_DATA'] = ("C:\\Users\\edwar\\Anaconda3\\Library\\share\\gdal")

    countries = get_countries()
    scenarios = get_scenarios()

    failures = []

    for idx, country in countries.iterrows():

        # if not country['iso3'] == 'RWA': #'GHA'
        #     continue

        print('-Working on {}'.format(country['iso3']))

        # process_flooding_layers(country, scenarios)

        process_surface_water_layers(country)

    print(failures)
