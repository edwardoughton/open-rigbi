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


def process_surface_water(country):
    """
    Load in intersecting raster layers, and export large
    water bodies as .shp.
    Parameters
    ----------
    country : string
        Country parameters.
    """
    output = []

    filename = 'surface_water.shp'
    folder = os.path.join(DATA_PROCESSED, country['iso3'], 'surface_water')
    path_out = os.path.join(folder, filename)
    if not os.path.exists(folder):
        os.makedirs(folder)

    path_national = os.path.join(DATA_PROCESSED, country['iso3'], 'national_outline.shp')

    if os.path.exists(path_national):
        polygon = gpd.read_file(path_national, crs='4326')
    else:
        print('Must Generate National Shapefile first')

    poly_bounds = polygon['geometry'].total_bounds
    poly_bbox = box(*poly_bounds, ccw = False)

    path_lc = os.path.join(DATA_RAW, 'global_surface_water')

    surface_files = [
        os.path.abspath(os.path.join(path_lc, f)
        ) for f in os.listdir(path_lc) if f.endswith('.tif')
    ]

    for surface_file in surface_files:

        path = os.path.join(path_lc, surface_file)

        src = rasterio.open(path, 'r+')

        tiff_bounds = src.bounds
        tiff_bbox = box(*tiff_bounds)

        if tiff_bbox.intersects(poly_bbox):

            print('-Working on {}'.format(surface_file))

            data = src.read()
            data[data < 10] = 0
            data[data >= 10] = 1
            polygons = rasterio.features.shapes(data, transform=src.transform)
            for poly, value in polygons:
                if value > 0:
                    output.append({
                        'geometry': poly,
                        'properties': {
                            'value': value
                        }
                    })


    output = gpd.GeoDataFrame.from_features(output, crs='epsg:4326')

    mask = output.area > country['threshold']
    output = output.loc[mask]

    filename = 'national_outline.shp'
    path = os.path.join(DATA_PROCESSED, country['iso3'], filename)
    national_outline = gpd.read_file(path, crs='epsg:4326')

    output = output.overlay(national_outline, how='intersection')

    mask = output.area > country['threshold']
    output = output.loc[mask]

    output.to_file(path_out, crs='epsg:4326')



if __name__ == "__main__":

    os.environ['GDAL_DATA'] = ("C:\\Users\\edwar\\Anaconda3\\Library\\share\\gdal")

    countries = get_countries()
    scenarios = get_scenarios()

    failures = []

    for idx, country in countries.iterrows():

        # if not iso3 == 'MLT': #'GHA'
        #     continue

        print('-Working on {}'.format(country['iso3']))

        # process_flooding_layers(country, scenarios)

        process_surface_water(country)

    print(failures)
