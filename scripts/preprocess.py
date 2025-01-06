"""
Preprocess sites data.

Ed Oughton

February 2022

"""
import sys
import os
import configparser
import json
import numpy as np
from shapely.ops import transform
from shapely.geometry import Point, box
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.mask import mask
import time
from tqdm import tqdm

from misc import (get_countries, process_country_shapes, 
                  process_regions, get_regions, get_scenarios)
from coastal_lut import process_coastal_lut

CONFIG = configparser.ConfigParser()
filename = 'script_config.ini'
CONFIG.read(os.path.join(os.path.dirname(__file__),'..', 'scripts', filename))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW = os.path.join(BASE_PATH, '..', '..', 'data_raw')
DATA_PROCESSED = os.path.join(BASE_PATH, 'processed')


def run_preprocessing(iso3):
    """
    Meta function for running preprocessing.

    """
    filename = "countries.csv"
    path = os.path.join(BASE_PATH, filename)

    countries = pd.read_csv(path, encoding='latin-1')
    country = countries[countries.iso3 == iso3]
    country = country.to_records('dicts')[0]
    regional_level = int(country['gid_region'])

    # print('Working on create_national_sites_csv')
    create_national_sites_csv(country)

    # print('Working on process_country_shapes')
    process_country_shapes(iso3)

    # print('Working on process_regions')
    process_regions(iso3, regional_level)

    # print('Working on gid_1 regional disaggregation')
    if regional_level >= 1:
        regions = get_regions(country, 1)#[:1]#[::-1]
        for region in regions:
            segment_by_gid_1(iso3, region['GID_1'])

    # print('Working on gid_2 disaggregation')
    if regional_level == 2:
        regions = get_regions(country, 2)#[:1]#[::-1]
        for region in regions:
            segment_by_gid_2(iso3, 2, region['GID_2'], region['GID_1'])

    process_coastal_lut(country)

    # print('Working on process_flooding_layers')
    process_flooding_layers(country)

    # print('Working on process_regional_flooding_layers')
    regions = get_regions(country, regional_level)#[:1]#[::-1]
    for region in regions:
        # if not region['GID_2'] == 'IND.2.12_1':
        #     continue
        region = region['GID_{}'.format(regional_level)]
        process_regional_flooding_layers(country, region)

    print('Convert cell estimates to site estimates')
    gid_id = "GID_{}".format(regional_level)
    regions = get_regions(country, regional_level)#[:1]#[::-1]
    for region in regions:
        create_sites_layer(
            country, 
            regional_level, 
            region[gid_id], 
            region['geometry']
        )

    return


def create_national_sites_csv(country):
    """
    Create a national sites csv layer for a selected country.

    """
    iso3 = country['iso3']#.values[0]

    filename = "mobile_codes.csv"
    path = os.path.join(BASE_PATH, filename)
    mobile_codes = pd.read_csv(path)
    mobile_codes = mobile_codes[['iso3', 'mcc', 'mnc']].drop_duplicates()
    all_mobile_codes = mobile_codes[mobile_codes['iso3'] == iso3]
    all_mobile_codes = all_mobile_codes.to_dict('records')

    output = []

    filename = '{}.csv'.format(iso3)
    folder = os.path.join(DATA_PROCESSED, iso3, 'sites')
    path_csv = os.path.join(folder, filename)

    # ### Produce national sites data layers
    if os.path.exists(path_csv):
        return

    # print('-site.csv data does not exist')
    # print('-Subsetting site data for {}'.format(iso3))

    if not os.path.exists(folder):
        os.makedirs(folder)

    filename = "cell_towers_2022-12-24.csv"
    path = os.path.join(DATA_RAW, filename)

    chunksize = 10 ** 6
    columns_to_load = ['radio', 'mcc', 'net', 'area', 'cell', 'unit', 'lon', 'lat']
    data_types = {'mcc': 'int32', 'net': 'int32', 'area': 'int32', 
                  'cell': 'int64', 'lon': 'float32', 'lat': 'float32'}
    output_path = os.path.join(DATA_PROCESSED, iso3, 'sites', '{}.csv'.format(iso3))

    relevant_mccs = {row['mcc'] for row in all_mobile_codes}  

    if not os.path.exists(output_path):
        seen = set()
        for idx, chunk in enumerate(pd.read_csv(path, usecols=columns_to_load, 
            dtype=data_types, chunksize=chunksize)):

            filtered_chunk = chunk[chunk['mcc'].isin(relevant_mccs)]
            
            for site in filtered_chunk.itertuples(index=False): 
                if site.cell in seen:
                    continue
                seen.add(site.cell)
                output.append({
                    'radio': site.radio,
                    'mcc': site.mcc,
                    'net': site.net,
                    'area': site.area,
                    'cell': site.cell,
                    'unit': site.unit,
                    'lon': site.lon,
                    'lat': site.lat
                })

        if output:
            pd.DataFrame(output).to_csv(path_csv, index=False)
            return


def segment_by_gid_1(iso3, region):
    """
    Segment sites by gid_1 bounding box.

    """
    gid_level = 'GID_1'

    filename = '{}.gpkg'.format(region)
    folder = os.path.join(DATA_PROCESSED, iso3, 'sites', 'gid_1', 'interim')
    if not os.path.exists(folder):
        os.makedirs(folder)
    path_out = os.path.join(folder, filename)

    if os.path.exists(path_out):
        return

    filename = '{}.csv'.format(iso3)
    folder = os.path.join(DATA_PROCESSED, iso3, 'sites')
    path = os.path.join(folder, filename)
    sites = pd.read_csv(path)#[:1000]
 
    geometry = [Point(xy) for xy in zip(sites["lon"], sites["lat"])]
    gdf = gpd.GeoDataFrame(sites, geometry=geometry)
    gdf.set_crs("EPSG:4326", inplace=True)  # EPSG:4326 is WGS 84 (lat/lon)
  
    filename = 'regions_{}_{}.gpkg'.format(1, iso3)
    folder = os.path.join(DATA_PROCESSED, iso3, 'regions')
    path_regions = os.path.join(folder, filename)
    regions = gpd.read_file(path_regions)#[:1]

    region_df = regions[regions[gid_level] == region]#['geometry'].values[0]

    if not hasattr(regions, 'sindex'):
        spatial_index = regions.sindex
    output = gpd.sjoin(gdf, region_df, how="inner", predicate="intersects")

    if len(output) > 0:
        output.set_crs("EPSG:4326", inplace=True)  # EPSG:4326 is WGS 84 (lat/lon)
        output.to_file(path_out, driver="GPKG")
    else:
        return


def segment_by_gid_2(iso3, level, region, gid_1):
    """
    Segment sites by gid_2 bounding box.

    """
    # Ensure output folder exists
    folder = os.path.join(DATA_PROCESSED, iso3, 'sites', 'gid_2', 'interim')
    os.makedirs(folder, exist_ok=True)
    path_out = os.path.join(folder, f'{region}.gpkg')
    if os.path.exists(path_out):
        return
    
    # Paths and file handling
    gid_level = f'GID_{level}'
    filename = f'regions_{level}_{iso3}.gpkg'
    folder = os.path.join(DATA_PROCESSED, iso3, 'regions')
    path = os.path.join(folder, filename)

    # Load regions and filter the specific region
    regions = gpd.read_file(path, where=f"{gid_level} = '{region}'")
    if regions.empty:
        return

    # Load sites data
    filename = f'{gid_1}.gpkg'
    folder = os.path.join(DATA_PROCESSED, iso3, 'sites', 'gid_1', 'interim')
    sites_path = os.path.join(folder, filename)
    if not os.path.exists(sites_path):
        # print(f"--Cannot find: {sites_path}")
        return

    # # Read only required columns
    sites = gpd.read_file(sites_path)

    regions = regions[['geometry']]
    sites = sites[['geometry', 'radio', 'mcc','net','area','cell']]
    output = gpd.sjoin(sites, regions, how="inner", predicate="intersects")

    if len(output) > 0:

        output.set_crs("EPSG:4326", inplace=True) 
        output.to_file(path_out, driver="GPKG")
    else:
        return
    
    return


def process_flooding_layers(country):
    """
    Loop to process all flood layers.

    """
    scenarios = get_scenarios()
    iso3 = country['iso3']
    name = country['country']
    hazard_dir = os.path.join(DATA_RAW, 'flood_hazard')

    failures = []

    for scenario in scenarios:#[:10]:

        filename = os.path.basename(scenario).replace('.tif','')
        path_in = os.path.join(hazard_dir, filename + '.tif')

        folder = os.path.join(DATA_PROCESSED, iso3, 'hazards', 'flooding')
        if not os.path.exists(folder):
            os.makedirs(folder)
        path_out = os.path.join(folder, filename + '.tif')

        if os.path.exists(path_out):
            continue

        # print('--{}: {}'.format(name, filename))

        if not os.path.exists(folder):
            os.makedirs(folder)

        try:
            process_flood_layer(country, path_in, path_out)
        except:
            # print('{} failed: {}'.format(country['iso3'], scenario))
            failures.append({
                 'iso3': country['iso3'],
                 'filename': filename
            })
            continue

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
    path_country = os.path.join(DATA_PROCESSED, iso3,
        'national_outline.gpkg')
    
    if not os.path.exists(path_country):
        # print('Must generate national_outline.gpkg first')
        return

    hazard = rasterio.open(path_in, 'r+', BIGTIFF='YES')
    hazard.nodata = 255
    hazard.crs.from_epsg(4326)

    national_outline = gpd.read_file(path_country)

    coords = [national_outline.geometry.iloc[0].__geo_interface__]
    out_img, out_transform = mask(hazard, coords, crop=True, all_touched=True)

    out_meta = hazard.meta.copy()

    out_meta.update({"driver": "GTiff",
                    "height": out_img.shape[1],
                    "width": out_img.shape[2],
                    "transform": out_transform,
                    "crs": 'epsg:4326',
                    "compress": 'lzw'})

    with rasterio.open(path_out, "w", **out_meta) as dest:
            dest.write(out_img)

    return


def process_regional_flooding_layers(country, region):
    """
    Process each flooding layer at the regional level.
    """
    scenarios = get_scenarios()
    iso3 = country['iso3']
    name = country['country']

    filename = 'coastal_lookup.csv'
    folder = os.path.join(DATA_PROCESSED, iso3, 'coastal')
    path_coastal = os.path.join(folder, filename)
    if not os.path.exists(path_coastal):
        coastal_lut = []
    else:
        coastal_lut = pd.read_csv(path_coastal)
        coastal_lut = list(coastal_lut['gid_id'])

    hazard_dir = os.path.join(DATA_PROCESSED, iso3, 'hazards', 'flooding')
    
    for scenario in scenarios:

        if 'inuncoast' in scenario and region not in coastal_lut:
            # print('Not a coastal region: {}'.format(region))
            continue

        filename = os.path.basename(scenario).replace('.tif','')
        path_in = os.path.join(hazard_dir, filename + '.tif')

        if not os.path.exists(path_in):
            continue

        folder = os.path.join(DATA_PROCESSED, iso3, 'hazards', 'flooding', 'regional')
        if not os.path.exists(folder):
            os.makedirs(folder)
        path_out = os.path.join(folder, region + '_' + filename + '.tif')

        if os.path.exists(path_out):
            continue

        # print('--{}: {}'.format(region, filename))
        try:
            process_regional_flood_layer(country, region, path_in, path_out)
        except:
        #     # print('{} failed: {}'.format(region, scenario))
            continue

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
    regional_level = int(country['gid_region'])
    gid_level = 'GID_{}'.format(regional_level)

    hazard = rasterio.open(path_in, 'r+', BIGTIFF='YES')
    hazard.nodata = 255
    hazard.crs.from_epsg(4326)

    iso3 = country['iso3']
    filename = 'regions_{}_{}.gpkg'.format(regional_level, iso3)
    path_country = os.path.join(DATA_PROCESSED, iso3, 'regions', filename)

    if os.path.exists(path_country):
        regions = gpd.read_file(path_country)
        region = regions[regions[gid_level] == region]
    else:
        # print('Must generate national_outline.shp first' )
        return

    geo = gpd.GeoDataFrame()
    geo = gpd.GeoDataFrame({'geometry': region['geometry']})
    coords = [json.loads(geo.to_json())['features'][0]['geometry']]

    out_img, out_transform = mask(hazard, coords, crop=True)

    depths = []
    for idx, row in enumerate(out_img[0]):
        for idx2, i in enumerate(row):
            if i > 0.001 and i < 150:
                # coords = raster.transform * (idx2, idx)
                depths.append(i)
            else:
                continue

    # if sum(depths) < 0.01:
    #     return

    out_meta = hazard.meta.copy()

    out_meta.update({"driver": "GTiff",
                    "height": out_img.shape[1],
                    "width": out_img.shape[2],
                    "transform": out_transform,
                    "crs": 'epsg:4326'})

    with rasterio.open(path_out, "w", **out_meta) as dest:
            dest.write(out_img)

    return


def create_sites_layer(country, regional_level, region, polygon):
    """
    Process cell estimates into an estimated site layer.

    """
    gid_level = "gid_{}".format(regional_level)
    filename = "{}_unique.gpkg".format(region)
    folder = os.path.join(DATA_PROCESSED, country['iso3'], 'sites', gid_level)
    path_out = os.path.join(folder, filename)
    
    if os.path.exists(path_out):
        return

    filename = "{}.gpkg".format(region)
    folder = os.path.join(DATA_PROCESSED, country['iso3'], 'sites', gid_level, 'interim')
    path = os.path.join(folder, filename)
    if not os.path.exists(path):
        return #print(f'Could not find {path}')
    data = gpd.read_file(path)#[:500]

    data['bs_id_float'] = data['cell'] / 256
    data['bs_id_int'] = np.round(data['bs_id_float'],0)
    data['sector_id'] = data['bs_id_float'] - data['bs_id_int']
    data['sector_id'] = np.round(data['sector_id'].abs() * 256)
    # data.to_csv(path_out, index=False)
    data['longitude'] = data['geometry'].x
    data['latitude'] = data['geometry'].y

    output = (
        data.groupby(['net', 'bs_id_int', 'radio']).agg(
            latitude=('latitude', 'mean'),
            longitude=('longitude', 'mean')
        )
    )

    geometry = [Point(xy) for xy in zip(output["longitude"], output["latitude"])]
    output = gpd.GeoDataFrame(output, geometry=geometry)
    output.set_crs("EPSG:4326", inplace=True)  # EPSG:4326 is WGS 84 (lat/lon)
    output.to_file(path_out, driver='GPKG')

    return


if __name__ == "__main__":

    # start_time = time.time()
    # args = sys.argv
    # iso3 = args[1]
    # print('Running site processing for {}'.format(iso3))
    # run_preprocessing(iso3)
    # end_time = time.time()
    # elapsed_time = end_time - start_time
    # print(f"Function executed in {elapsed_time:.2f} seconds")

    countries = get_countries()

    failures = []
    for country in tqdm(countries):

        # if not country['iso3'] == 'ALB':
        #    continue

        print(f"--{country['country']}")#['iso3']

        try:
            run_preprocessing(country['iso3'])

        except:
            failures.append((country['iso3'],country['country']))
        print(failures)
