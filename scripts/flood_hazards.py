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

from misc import get_countries, get_scenarios, get_regions, remove_small_shapes

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

    failures = [] 

    for scenario in scenarios[::-1]:

        #if 'river' in scenario:
        #    continue

        #if not os.path.basename(scenario) == 'inuncoast_rcp8p5_wtsub_2080_rp1000_0.tif':
        #    continue

        filename = os.path.basename(scenario).replace('.tif','')
        path_in = os.path.join(hazard_dir, filename + '.tif')

        folder = os.path.join(DATA_PROCESSED, iso3, 'hazards', 'flooding')
        if not os.path.exists(folder):
            os.makedirs(folder)
        path_out = os.path.join(folder, filename + '.tif')

        #if not os.path.exists(path_out):

        print('--{}: {}'.format(name, filename))

        if not os.path.exists(folder):
            os.makedirs(folder)

        try:
            process_flood_layer(country, path_in, path_out)
        except:
            print('{} failed: {}'.format(country['iso3'], scenario))         
            failures.append({
                'iso3': country['iso3'],
                'filename': filename
            })
            continue
        print(failures)
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
    print(hazard)
    hazard.nodata = 255
    hazard.crs.from_epsg(4326)

    iso3 = country['iso3']
    path_country = os.path.join(DATA_PROCESSED, iso3,
        'national_outline.shp')

    if os.path.exists(path_country):
        country = gpd.read_file(path_country)
    else:
        print('Must generate national_outline.shp first' )

    #if os.path.exists(path_out):
    #    return
    #print(country)
    geo = gpd.GeoDataFrame()

    geo = gpd.GeoDataFrame({'geometry': country['geometry']})

    coords = [json.loads(geo.to_json())['features'][0]['geometry']]

    out_img, out_transform = mask(hazard, coords, crop=True)

    out_meta = hazard.meta.copy()

    out_meta.update({"driver": "GTiff",
                    "height": out_img.shape[1],
                    "width": out_img.shape[2],
                    "transform": out_transform,
                    "crs": 'epsg:4326',
                    "compress": 'lzw'})
    #print(path_out)
    with rasterio.open(path_out, "w", **out_meta) as dest:
            dest.write(out_img)

    return


def process_regional_flooding_layers(country, region, scenarios):
    """
    Process each flooding layer at the regional level.

    """
    iso3 = country['iso3']
    name = country['country']

    hazard_dir = os.path.join(DATA_PROCESSED, iso3, 'hazards', 'flooding')

    for scenario in scenarios:

        #if 'river' in scenario:
        #    continue

        #if not os.path.basename(scenario) == 'inuncoast_rcp8p5_wtsub_2080_rp1000_0.tif':
        #    continue

        filename = os.path.basename(scenario).replace('.tif','')
        path_in = os.path.join(hazard_dir, filename + '.tif')

        folder = os.path.join(DATA_PROCESSED, iso3, 'hazards', 'flooding', 'regional')
        if not os.path.exists(folder):
            os.makedirs(folder)
        path_out = os.path.join(folder, region + '_' + filename + '.tif')

        if not os.path.exists(path_out):

            #print('--{}: {}'.format(name, filename))

            #if not os.path.exists(folder):
            #    os.makedirs(folder)
            #print(path_in)
            try:
                process_regional_flood_layer(country, region, path_in, path_out)
            except:
                print('{} failed: {}'.format(country['iso3'], scenario))
                continue

            #failures.append({
            #     'iso3': iso3,
            #     'filename': filename
            #})

    return


def process_regional_flood_layer(country, region, path_in, path_out):
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
    gid_level = 'GID_{}'.format(regional_level)
    #print(path_in, region)
    hazard = rasterio.open(path_in, 'r+', BIGTIFF='YES')
    hazard.nodata = 255
    hazard.crs.from_epsg(4326)
    #print(hazard)
    iso3 = country['iso3']
    filename = 'regions_{}_{}.shp'.format(regional_level, iso3)
    path_country = os.path.join(DATA_PROCESSED, iso3, 'regions', filename)

    if os.path.exists(path_country):
        regions = gpd.read_file(path_country)
        region = regions[regions[gid_level] == region]
    else:
        print('Must generate national_outline.shp first' )
        return
    #print(regions)
    geo = gpd.GeoDataFrame()

    geo = gpd.GeoDataFrame({'geometry': region['geometry']})

    coords = [json.loads(geo.to_json())['features'][0]['geometry']]

    out_img, out_transform = mask(hazard, coords, crop=True)

    out_meta = hazard.meta.copy()

    out_meta.update({"driver": "GTiff",
                    "height": out_img.shape[1],
                    "width": out_img.shape[2],
                    "transform": out_transform,
                    "crs": 'epsg:4326'})
    #print(path_out)
    with rasterio.open(path_out, "w", **out_meta) as dest:
            dest.write(out_img)

    return


def process_flooding_extent_stats(country, region, scenarios):
    """
    Get aggregate statistics on flooding extent by region.

    """
    #print('Working on {}'.format(country['iso3']))
    folder = os.path.join(DATA_PROCESSED, country['iso3'], 'hazards', 'flooding', 'regional')

    for scenario_path in scenarios:#[:1]:

        #if not 'inuncoast_rcp8p5_wtsub_2080_rp1000_0' in scenario_path:
        #    continue
        
        print(scenario_path)
        filename = os.path.basename(scenario_path).replace('.tif','')
        #print(filename)
        folder_out = os.path.join(DATA_PROCESSED,'results','validation','country_data',
            country['iso3'], 'regional', filename)

        if not os.path.exists(folder_out):
            os.makedirs(folder_out)

        path_out = os.path.join(folder_out, region + '_' + filename + '.csv')

        if os.path.exists(path_out):
            continue

        print('Working on {}'.format(filename))

        metrics = []

        path = os.path.join(folder,  region + '_' + filename + '.tif')
        
        if not os.path.exists(path):
            print('path does not exist: {}'.format(path))
            continue

        try:
            raster = rasterio.open(path)
            data = raster.read(1)
        except:
            print('reading failed {}'.format(filename))
            continue

        output = []
        depths = []

        #print('working on raster loops')
        for idx, row in enumerate(data):
            for idx2, i in enumerate(row):
                if i > 0 and i < 150:
                    coords = raster.transform * (idx2, idx)
                    depths.append(i)

        depths.sort()

        if 'river' in filename:
            hazard = filename.split('_')[0]
            climate_scenario = filename.split('_')[1]
            model = filename.split('_')[2]
            year = filename.split('_')[3]
            return_period = filename.split('_')[4]#[:-4]
            percentile = '-'

        if 'coast' in filename:
            hazard = filename.split('_')[0]
            climate_scenario = filename.split('_')[1]
            model = filename.split('_')[2]
            year = filename.split('_')[3]
            return_period = filename.split('_')[4]
            remaining_portion = filename.split('_')[5]
            if remaining_portion == '0':
                percentile = 0
            else:
                percentile = filename.split('_')[7]#[:-4]

        if len(depths) == 0:
            continue
        #print('writing metrics')
        metrics.append({
            'hazard': hazard,
            'climate_scenario': climate_scenario,
            'model': model,
            'year': year,
            'return_period': return_period,
            'percentile': percentile,
            'min_depth': round(min(depths),2),
            'mean_depth': sum(depths) / len(depths),
            'median_depth': depths[len(depths)//2],
            'max_depth': max(depths),
            'flooded_area_km2': len(depths),
        })
        #print('converting to df')
        metrics = pd.DataFrame(metrics)
        #filename = "{}.csv".format(filename[:-4])
        #print('writing to csv: {}'.format(path_out))
        metrics.to_csv(path_out, index=False)

    return


def process_surface_water(country, region):
    """
    Load in intersecting raster layers, and export large
    water bodies as .shp.

    Parameters
    ----------
    country : string
        Country parameters.

    """
    level = country['gid_region']
    gid_id = 'GID_{}'.format(level)

    filename = 'regions_{}_{}.shp'.format(level, country['iso3'])
    folder = os.path.join(DATA_PROCESSED, country['iso3'], 'regions')
    path = os.path.join(folder, filename)
    regions = gpd.read_file(path, crs='epsg:4326')
    polygon = regions[regions[gid_id] == region]

    filename = '{}.shp'.format(region)
    folder = os.path.join(DATA_PROCESSED, country['iso3'], 'surface_water', 'regions')
    path_out = os.path.join(folder, filename)
    if not os.path.exists(folder):
        os.makedirs(folder)

    poly_bounds = polygon['geometry'].total_bounds
    poly_bbox = box(*poly_bounds, ccw = False)

    path_lc = os.path.join(DATA_RAW, 'global_surface_water', 'chopped')

    surface_files = [
        os.path.abspath(os.path.join(path_lc, f)
        ) for f in os.listdir(path_lc) if f.endswith('.tif')
    ]

    output = []

    for surface_file in surface_files:

        # print(os.path.basename(surface_file))
        # if not os.path.basename(surface_file) in [
        #     # 'occurrence_20E_0Nv1_3_2020.tif',
        #     'occurrence_30E_0Nv1_3_2020_0_0.tif'
        #     ]:
        #     continue

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

    #folder = os.path.join(DATA_PROCESSED, country['iso3'], 'surface_water', 'regions')
    #output.to_file(os.path.join(folder, 'test.shp'), crs='epsg:4326')

    mask = output.area > .0001 #country['threshold']
    output = output.loc[mask]

    output = gpd.overlay(output, polygon, how='intersection')

    output['geometry'] = output.apply(remove_small_shapes, axis=1)

    mask = output.area > .0001 #country['threshold']
    output = output.loc[mask]

    output.to_file(path_out, crs='epsg:4326')

    return


if __name__ == "__main__":

    os.environ['GDAL_DATA'] = ("C:\\Users\\edwar\\Anaconda3\\Library\\share\\gdal")

    countries = get_countries()
    scenarios = get_scenarios()

    # failures = []

    for idx, country in countries.iterrows():

        if not country['iso3'] in ['USA',#'ARG',
            #'BEL','BIH','BRB','EST','GUM','KHM','LSO','TWN','VGB', 'AND',
            #'BFA','UBZ','BMU','BTN','CYM','DJI','FRO','ISR','KNA','LCA','MLI','MNG','MUS','PRY','TCA','WSM'
            ]: #'GHA'
            continue
        #print(country)
        print('-Working on {}'.format(country['iso3']))

        #process_flooding_layers(country, scenarios)


        # regions = [
        #     'RWA.1_1',
        #     'RWA.2_1',
        #     'RWA.3_1',
        #     'RWA.4_1',
        #     'RWA.5_1',
        # ]

        regions = get_regions(country, country['gid_region'])
        for idx, region in regions.iterrows():
                    
            
            region = region['GID_{}'.format(country['gid_region'])]
            #if not 'USA.51.' in region:# or not 'USA.51.' in region:
            #    continue

            #print('processing regional extent for : {}'.format(region))
            process_regional_flooding_layers(country, region, scenarios)
            process_flooding_extent_stats(country, region, scenarios)
     #print(failures)
