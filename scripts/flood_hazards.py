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
import rasterio.merge
import glob
from shapely.geometry import box

from misc import get_countries, get_scenarios, remove_small_shapes

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


def process_surface_water_layers(country, region):
    """
    Loop to process all water mask layers.
    """

    # process_country_level(country)

    process_regional_level(country, region)

    return


def process_country_level(country):
    """
    Process at the country level.

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

    return print('failures: {}'.format(failures))


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
    Merge raster layers into single country layer.

    """
    folder = os.path.join(DATA_PROCESSED, country['iso3'], 'surface_water')
    path_out = os.path.join(folder, 'surface_water.tif')

    if os.path.exists(path_out):
        return

    folder = os.path.join(DATA_PROCESSED, country['iso3'], 'surface_water')
    paths = glob.glob(os.path.join(folder, "*.tif"))#[:5]

    data = []

    for path in paths:
        interim = rasterio.open(path)
        data.append(interim)

    dest, output_transform = rasterio.merge.merge(
        #data, bounds, res, nodata, precision
        data, None, None, None, 7
        )

    with rasterio.open(path) as src:
            out_meta = src.meta.copy()

    out_meta.update({"driver": "GTiff",
                    "height": dest.shape[1],
                    "width": dest.shape[2],
                    "transform": output_transform})

    with rasterio.open(path_out, "w", **out_meta) as dest1:
            dest1.write(dest)

    return


def process_regional_level(country, region):
    """
    Cut raster at regional level.

    """
    level = country['gid_region']
    gid_id = 'GID_{}'.format(level)

    filename = 'regions_{}_{}.shp'.format(level, country['iso3'])
    folder = os.path.join(DATA_PROCESSED, country['iso3'], 'regions')
    path = os.path.join(folder, filename)
    regions = gpd.read_file(path, crs='epsg:4326')[:1]

    folder = os.path.join(DATA_PROCESSED, country['iso3'], 'surface_water')
    path_in = os.path.join(folder, 'surface_water.tif')

    folder_out = os.path.join(DATA_PROCESSED, country['iso3'], 'surface_water', 'regions')
    if not os.path.exists(folder_out):
        os.mkdir(folder_out)

    folder = os.path.join(DATA_PROCESSED, country['iso3'], 'surface_water')
    path_out = os.path.join(folder, 'surface_water.shp')

    output = []

    for idx, region in regions.iterrows():

        region_id = region[gid_id]

        # path_out = os.path.join(folder_out, '{}.tif'.format(region_id))

        # if os.path.exists(path_out):
        #     continue

        geom = region['geometry']

        # process_regional_water_layer(path_in, path_out, geom)
        src = rasterio.open(path_in, 'r+')
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

    mask = output.area > .0001 #country['threshold']
    output = output.loc[mask]

    filename = 'national_outline.shp'
    path = os.path.join(DATA_PROCESSED, country['iso3'], filename)
    national_outline = gpd.read_file(path, crs='epsg:4326')

    output = gpd.overlay(output, national_outline, how='intersection')

    output['geometry'] = output.apply(remove_small_shapes, axis=1)

    mask = output.area > .0001 #country['threshold']
    output = output.loc[mask]

    output.to_file(path_out, crs='epsg:4326')

    return


def process_regional_water_layer(path_in, path_out, geometry):
    """
    Clip the water layer to the chosen regional boundary
    and place in desired country folder.

    """
    hazard = rasterio.open(path_in, 'r+')
    hazard.nodata = 255
    hazard.crs.from_epsg(4326)

    data = src.read()
    data[data < 10] = 0
    data[data >= 10] = 1

    geo = gpd.GeoDataFrame()

    geo = gpd.GeoDataFrame({'geometry': geometry}, index=[0])

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

    countries = get_countries()
    scenarios = get_scenarios()

    failures = []

    for idx, country in countries.iterrows():

        if not country['iso3'] == 'RWA': #'GHA'
            continue

        print('-Working on {}'.format(country['iso3']))

        # process_flooding_layers(country, scenarios)

        process_surface_water_layers(country, 'RWA.1_1')

    print(failures)
