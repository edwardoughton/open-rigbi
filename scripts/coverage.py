"""
Coverage Analysis.

Written by Ed Oughton.

April 2022.

"""
import os
import configparser
import random
import json
import glob
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.mask import mask
from rasterio import features
from tqdm import tqdm
from shapely.geometry import shape, Point, Polygon, mapping, LineString, MultiPolygon
from rasterstats import zonal_stats
import math
import pyproj
from shapely.ops import transform

from prop import get_sinr
from misc import params, technologies, get_countries, get_regions, get_scenarios

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW = os.path.join(BASE_PATH, 'raw')
DATA_PROCESSED = os.path.join(BASE_PATH, 'processed')


def create_national_sites_layer(country):
    """
    Create a national sites layer for a selected country.

    """
    filename = '{}.shp'.format(country['iso3'])
    folder = os.path.join(DATA_PROCESSED, country['iso3'], 'sites')
    path_shp = os.path.join(folder, filename)

    if os.path.exists(path_shp):
        return

    filename = '{}.csv'.format(country['iso3'])
    path_csv = os.path.join(folder, filename)

    if not os.path.exists(path_csv):

        print('--Creating site.csv data.')

        if not os.path.exists(folder):
            os.makedirs(folder)

        filename = "cell_towers_2022-02-02-T000000.csv"
        folder = "../../../site_location_data/OpenCellID"
        path = os.path.join(folder, filename)
        all_data = pd.read_csv(path)#[:10]

        country_data = all_data.loc[all_data['mcc'] == country['mcc']]

        if len(country_data) == 0:
            print('--{} had no data'.format(country['name']))
            return

        country_data.to_csv(path_csv, index=False)

    if os.path.exists(path_csv):

        country_data = pd.read_csv(path_csv)#[:10]

        output = []

        for idx, row in tqdm(country_data.iterrows(), total=country_data.shape[0]):
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

        output = gpd.GeoDataFrame.from_features(output, crs=crs)
        output.to_file(path_shp)

    return


def process_regional_sites_layer(country, region):
    """
    Create regional site layers.

    """
    iso3 = country['iso3']
    regional_level = country['lowest']
    gid_level = 'GID_{}'.format(regional_level)
    gid_id = region[gid_level]

    filename = '{}.shp'.format(gid_id)
    folder = os.path.join(DATA_PROCESSED, iso3, 'regional_data', gid_id, 'sites')
    if not os.path.exists(folder):
        os.makedirs(folder)
    path = os.path.join(folder, filename)

    if os.path.exists(path):
        return

    filename = '{}.shp'.format(iso3)
    folder = os.path.join(DATA_PROCESSED, iso3, 'sites')
    path_shp = os.path.join(folder, filename)
    sites = gpd.read_file(path_shp, crs=crs)

    output = []

    for idx, site in sites.iterrows():
        if region['geometry'].intersects(site['geometry']):
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
                    'cell_id': '{}_{}'.format(
                            round(site['geometry'].coords.xy[0][0], 6),
                            round(site['geometry'].coords.xy[1][0], 6)
                    ),
                }
            })

    if len(output) > 0:

        output = gpd.GeoDataFrame.from_features(output, crs='epsg:4326')
        output.to_file(path)

    return


def process_tech_specific_sites(country, region, technologies):
    """
    Break sites into tech-specific shapefiles.

    """
    iso3 = country['iso3']
    regional_level = country['lowest']
    gid_level = 'GID_{}'.format(regional_level)
    gid_id = region[gid_level]

    filename = '{}.shp'.format(gid_id)
    folder = os.path.join(DATA_PROCESSED, iso3, 'regional_data', gid_id, 'sites')
    path = os.path.join(folder, filename)
    if not os.path.exists(path):
        return
    sites = gpd.read_file(path, crs='epsg:4326')

    for technology in technologies:

        filename = '{}_{}.shp'.format(technology, gid_id)
        folder = os.path.join(DATA_PROCESSED, iso3, 'regional_data', gid_id,
            'sites')
        if not os.path.exists(folder):
            os.mkdir(folder)
        path = os.path.join(folder, filename)

        if os.path.exists(path):
            return

        output = []

        for idx, site in sites.iterrows():
            if technology == site['radio']:
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
                        'cell_id': '{}_{}'.format(
                            round(site['geometry'].coords.xy[0][0], 6),
                            round(site['geometry'].coords.xy[1][0], 6)
                        ),
                    }
                })

        if len(output) > 0:

            output = gpd.GeoDataFrame.from_features(output, crs='epsg:4326')
            output.to_file(path)

    return


def process_country_shapes(country):
    """
    Creates a single national boundary for the desired country.

    Parameters
    ----------
    country : dict
        Contains all desired country information.

    """
    iso3 = country['iso3']

    path = os.path.join(DATA_PROCESSED, iso3)

    if os.path.exists(os.path.join(path, 'national_outline.shp')):
        return 'Completed national outline processing'

    if not os.path.exists(path):
        os.makedirs(path)

    shape_path = os.path.join(path, 'national_outline.shp')

    path = os.path.join(DATA_RAW, 'gadm36_levels_shp', 'gadm36_0.shp')
    countries = gpd.read_file(path)

    single_country = countries[countries.GID_0 == iso3].reset_index()

    # # if not iso3 == 'MDV':
    single_country['geometry'] = single_country.apply(
        remove_small_shapes, axis=1)

    glob_info_path = os.path.join(DATA_RAW, 'countries.csv')
    load_glob_info = pd.read_csv(glob_info_path, encoding = "ISO-8859-1",
        keep_default_na=False)
    single_country = single_country.merge(
        load_glob_info, left_on='GID_0', right_on='iso3')

    single_country.to_file(shape_path, driver='ESRI Shapefile')

    return


def remove_small_shapes(x):
    """
    Remove small multipolygon shapes.

    Parameters
    ---------
    x : polygon
        Feature to simplify.

    Returns
    -------
    MultiPolygon : MultiPolygon
        Shapely MultiPolygon geometry without tiny shapes.

    """
    if x.geometry.type == 'Polygon':
        return x.geometry

    elif x.geometry.type == 'MultiPolygon':

        area1 = 0.01
        area2 = 50

        if x.geometry.area < area1:
            return x.geometry

        if x['GID_0'] in ['CHL','IDN']:
            threshold = 0.01
        elif x['GID_0'] in ['RUS','GRL','CAN','USA']:
            threshold = 0.01
        elif x.geometry.area > area2:
            threshold = 0.1
        else:
            threshold = 0.001

        new_geom = []
        for y in list(x['geometry'].geoms):
            if y.area > threshold:
                new_geom.append(y)

        return MultiPolygon(new_geom)


def process_regions(country):
    """
    Function for processing the lowest desired subnational
    regions for the chosen country.

    Parameters
    ----------
    country : dict
        Contains all desired country information.

    """
    regions = []

    iso3 = country['iso3']
    level = country['lowest']

    for regional_level in range(1, level + 1):

        filename = 'regions_{}_{}.shp'.format(regional_level, iso3)
        folder = os.path.join(DATA_PROCESSED, iso3, 'regions')
        path_processed = os.path.join(folder, filename)

        if os.path.exists(path_processed):
            continue

        if not os.path.exists(folder):
            os.mkdir(folder)

        filename = 'gadm36_{}.shp'.format(regional_level)
        path_regions = os.path.join(DATA_RAW, 'gadm36_levels_shp', filename)
        regions = gpd.read_file(path_regions)

        regions = regions[regions.GID_0 == iso3]

        regions = regions.copy()
        regions["geometry"] = regions.geometry.simplify(
            tolerance=0.001, preserve_topology=True)

        regions['geometry'] = regions.apply(remove_small_shapes, axis=1)

        try:
             regions.to_file(path_processed, driver='ESRI Shapefile')
        except:
            print('Unable to write {}'.format(filename))
            pass

    return


def process_settlement_layer(country):
    """
    Clip the settlement layer to the chosen country boundary
    and place in desired country folder.

    Parameters
    ----------
    country : dict
        Contains all desired country information.

    """
    iso3 = country['iso3']
    # regional_level = country['gid_region']

    path_settlements = os.path.join(DATA_RAW, 'settlement_layer',
        'ppp_2020_1km_Aggregated.tif')

    settlements = rasterio.open(path_settlements, 'r+')
    settlements.nodata = 255
    settlements.crs.from_epsg(4326)

    iso3 = country['iso3']
    path_country = os.path.join(DATA_PROCESSED, iso3,
        'national_outline.shp')

    if os.path.exists(path_country):
        country = gpd.read_file(path_country)
    else:
        print('Must generate national_outline.shp first' )

    shape_path = os.path.join(DATA_PROCESSED, iso3, 'settlements.tif')

    if os.path.exists(shape_path):
        return

    geo = gpd.GeoDataFrame({'geometry': country.geometry})
    coords = [json.loads(geo.to_json())['features'][0]['geometry']]

    out_img, out_transform = mask(settlements, coords, crop=True)
    out_meta = settlements.meta.copy()
    out_meta.update({"driver": "GTiff",
                    "height": out_img.shape[1],
                    "width": out_img.shape[2],
                    "transform": out_transform,
                    "crs": 'epsg:4326'})

    with rasterio.open(shape_path, "w", **out_meta) as dest:
            dest.write(out_img)

    return


def get_regional_data(country, regions):
    """
    Extract regional data including luminosity and population.

    Parameters
    ----------
    country : dict
        Contains all desired country information.

    """
    iso3 = country['iso3']
    level = country['lowest']
    gid_level = 'GID_{}'.format(level)

    filename = 'regional_data.csv'
    path_output = os.path.join(DATA_PROCESSED, iso3, filename)

    if os.path.exists(path_output):
        return

    results = []

    for idx, region in tqdm(regions.iterrows(), total=regions.shape[0]):

        path_pop = os.path.join(DATA_PROCESSED, iso3, 'regional_data',
            region[gid_level], 'settlements','settlements.tif')

        with rasterio.open(path_pop) as src:

            affine = src.transform
            array = src.read(1)
            array[array <= 0] = 0

            population = [d['sum'] for d in zonal_stats(
                region['geometry'],
                array,
                stats=['sum'],
                nodata=0,
                affine=affine)][0]

        area_km2 = round(area_of_polygon(region['geometry']) / 1e6)

        if population == None:
            population = 0

        # if area_km2 == 0:
        #     continue

        results.append({
            'GID_0': region['GID_0'],
            'GID_id': region[gid_level],
            'GID_level': gid_level,
            'population_total': population,
            'area_km2': area_km2,
            'pop_density_km2': population / area_km2,
        })

    results_df = pd.DataFrame(results)

    results_df.to_csv(path_output, index=False)

    return


def area_of_polygon(geom):
    """
    Returns the area of a polygon. Assume WGS84 as crs.

    """
    geod = pyproj.Geod(ellps="WGS84")

    poly_area, poly_perimeter = geod.geometry_area_perimeter(
        geom
    )

    return abs(poly_area)


def cut_surface_water_layers(country, region):
    """
    Cut the settlement layer by each regional shape

    """
    #This needs to be based on the outline of the region.
    filename = 'occurrence_30E_10Sv1_3_2020.tif'
    folder = os.path.join(DATA_PROCESSED, country['iso3'], 'surface_water')
    path = os.path.join(folder, filename)

    surface_water = rasterio.open(path, 'r+')
    surface_water.nodata = 255
    surface_water.crs.from_epsg(4326)

    folder = os.path.join(DATA_PROCESSED, country['iso3'], 'regional_data',
        region['GID_{}'.format(country['lowest'])], 'surface_water')
    shape_path = os.path.join(folder, 'surface_water.tif')

    if os.path.exists(shape_path):
        return

    if not os.path.exists(folder):
        os.makedirs(folder)

    if region['geometry'].type == 'Polygon':
        geo = gpd.GeoDataFrame({'geometry': region['geometry']}, index=[0])
    elif region['geometry'].type == 'MultiPolygon':
        geo = gpd.GeoDataFrame()
        for idx, item in enumerate(list(region['geometry'].geoms)):
            geo = geo.append({'geometry': item}, ignore_index=True)

    coords = [json.loads(geo.to_json())['features'][0]['geometry']]

    out_img, out_transform = mask(surface_water, coords, crop=True)
    out_meta = surface_water.meta.copy()
    out_meta.update({"driver": "GTiff",
                    "height": out_img.shape[1],
                    "width": out_img.shape[2],
                    "transform": out_transform,
                    "crs": 'epsg:4326'})

    with rasterio.open(shape_path, "w", **out_meta) as dest:
            dest.write(out_img)

    return


def cut_settlement_layers(country, region):
    """
    Cut the settlement layer by each regional shape

    """
    path = os.path.join(DATA_PROCESSED, country['iso3'], 'settlements.tif')

    settlements = rasterio.open(path, 'r+')
    settlements.nodata = 255
    settlements.crs.from_epsg(4326)

    folder = os.path.join(DATA_PROCESSED, country['iso3'], 'regional_data',
        region['GID_{}'.format(country['lowest'])], 'settlements')
    shape_path = os.path.join(folder, 'settlements.tif')

    if os.path.exists(shape_path):
        return

    if not os.path.exists(folder):
        os.makedirs(folder)

    if region['geometry'].type == 'Polygon':
        geo = gpd.GeoDataFrame({'geometry': region['geometry']}, index=[0])
    elif region['geometry'].type == 'MultiPolygon':
        geo = gpd.GeoDataFrame()
        for idx, item in enumerate(list(region['geometry'].geoms)):
            geo = geo.append({'geometry': item}, ignore_index=True)

    coords = [json.loads(geo.to_json())['features'][0]['geometry']]

    out_img, out_transform = mask(settlements, coords, crop=True)
    out_meta = settlements.meta.copy()
    out_meta.update({"driver": "GTiff",
                    "height": out_img.shape[1],
                    "width": out_img.shape[2],
                    "transform": out_transform,
                    "crs": 'epsg:4326'})

    with rasterio.open(shape_path, "w", **out_meta) as dest:
            dest.write(out_img)

    return


def convert_to_shapes(country, region):
    """
    Convert settlement raster to vector shapefile by region.

    """
    folder = os.path.join(
        DATA_PROCESSED,
        country['iso3'],
        'regional_data',
        region['GID_{}'.format(country['lowest'])],
        'settlements'
    )
    path_out = os.path.join(folder, 'tile_points.shp')

    if os.path.exists(path_out):
        return

    shape_path = os.path.join(folder, 'settlements.tif')
    settlements = rasterio.open(shape_path, 'r+')
    settlements.nodata = 255
    settlements.crs.from_epsg(4326)
    data = settlements.read(1)

    output = []

    for geom, value in features.shapes(data, transform=settlements.transform):

        geom = rasterio.warp.transform_geom(
            settlements.crs, 'EPSG:4326', geom, precision=6)

        geom_centroid = shape(geom).centroid

        if value == 255:
            continue

        if region['geometry'].contains(geom_centroid):

            output.append({
                'geometry': geom_centroid,
                'properties': {
                    'point_id': '{}-{}'.format(
                        round(geom_centroid.coords.xy[0][0], 6),
                        round(geom_centroid.coords.xy[1][0], 6)
                    ),
                    'value': value
                }
            })

    if len(output) == 0:
        return

    output = gpd.GeoDataFrame.from_features(output, crs='EPSG:4326')
    output.to_file(path_out)

    return


def write_as_text(country, region):
    """
    Write out points layer as text.

    """
    GID_level = 'GID_{}'.format(country['lowest'])
    gid_id = region[GID_level]

    folder = os.path.join(DATA_PROCESSED, country['iso3'],
        'regional_data', gid_id, 'settlements')

    path_out = os.path.join(folder, 'tile_points.csv')

    if os.path.exists(path_out):
        return

    path_in = os.path.join(folder, 'tile_points.shp')

    if not os.path.exists(path_out):
        return

    data = gpd.read_file(path_in, crs='epsg:4326')

    project = pyproj.Transformer.from_proj(
        pyproj.Proj('epsg:4326'), # source coordinate system
        pyproj.Proj('epsg:3857')) # destination coordinate system

    output = []

    for idx, point in data.iterrows():

        geom_4326 = point['geometry']

        geom_3857 = transform(project.transform, geom_4326) # apply projection

        output.append({
            'GID_id': gid_id,
            'GID_level': GID_level,
            'point_value': point['value'],
            'point_id_4326': '{}_{}'.format(
                geom_4326.coords.xy[0][0],
                geom_4326.coords.xy[1][0]
            ),
            'point_id_3857': '{}_{}'.format(
                geom_3857.coords.xy[0][0],
                geom_3857.coords.xy[1][0]
            ),
        })

    if len(output) == 0:
        return

    output = pd.DataFrame(output)
    output.to_csv(path_out, index=False)

    return


def calculate_distances_lut(country, region, technology):
    """
    Calculate distances.

    """
    folder = os.path.join(DATA_PROCESSED, country['iso3'],
        'regional_data', region['GID_{}'.format(country['lowest'])])

    path_out = os.path.join(folder, '{}_distance_lut.csv'.format(technology))

    if os.path.exists(path_out):
        return

    path_tile_points = os.path.join(folder, 'settlements', 'tile_points.shp')

    if not os.path.exists(path_tile_points):
        return

    tile_points = gpd.read_file(path_tile_points, crs='epsg:4326')#[100:101]
    tile_points = tile_points.to_crs(epsg=3857)

    path_sites = os.path.join(folder, 'sites',
        '{}_{}.shp'.format(technology, region['GID_{}'.format(country['lowest'])])
    )

    if not os.path.exists(path_sites):
        return

    sites = gpd.read_file(path_sites, crs='epsg:4326')#[:1]
    if len(sites) == 0:
        return
    sites = sites.to_crs(epsg=3857)

    output = []

    for idx, point in tqdm(tile_points.iterrows(), total=tile_points.shape[0]):

        # ## Get sites within x km of the point (e.g. 20 km)
        point_geom = point['geometry'].buffer(10000)
        point_buffer = gpd.GeoDataFrame(geometry=[point_geom], index=[0], crs='epsg:3857')

        if len(point_buffer) == 0:
            continue

        try:
            subset_sites = gpd.overlay(sites, point_buffer, how='intersection')
        except:
            continue

        if len(subset_sites) == 0:
            continue

        # ##
        single_point = gpd.GeoDataFrame(geometry=[point['geometry']], crs='epsg:3857')
        site_distances = subset_sites
        site_distances['distance'] = subset_sites.geometry.apply(lambda g: single_point.distance(g))

        if len(site_distances) >= 1:
            site_distances = site_distances.loc[site_distances['distance'] > 250]
            if len(site_distances) >= 1:
                site_distances = site_distances.sort_values('distance')[:params['number_of_cells']]
            else:
                continue
        else:
            continue

        site_distances = site_distances.reset_index(level=0)

        site1 = site_distances.iloc[[0]]
        site1_distance_m = site1['distance'].values[0]
        site1_id = site1['cell_id'].values[0]

        site2_distance_m = 0
        site2_id = 'N/A'

        site3_distance_m = 0
        site3_id = 'N/A'

        site4_distance_m = 0
        site4_id = 'N/A'

        if len(site_distances) >= 2:
            site2 = site_distances.iloc[[1]]
            site2_distance_m = site2['distance'].values[0]
            site2_id = site2['cell_id'].values[0]

        if len(site_distances) >= 3:
            site3 = site_distances.iloc[[2]]
            site3_distance_m = site3['distance'].values[0]
            site3_id = site3['cell_id'].values[0]

        if len(site_distances) >= 4:
            site4 = site_distances.iloc[[2]]
            site4_distance_m = site4['distance'].values[0]
            site4_id = site4['cell_id'].values[0]

        output.append({
            'point_value': point['value'],
            'point_id': '{}_{}'.format(
                point['geometry'].coords.xy[0][0],
                point['geometry'].coords.xy[1][0]
            ),
            'point_lon': point['geometry'].coords.xy[0][0],
            'point_lat': point['geometry'].coords.xy[1][0],
            'site1_distance_m': site1_distance_m,
            'site1_id': site1_id,
            'site2_distance_m': site2_distance_m,
            'site2_id': site2_id,
            'site3_distance_m': site3_distance_m,
            'site3_id': site3_id,
            'site4_distance_m': site4_distance_m,
            'site4_id': site4_id,
        })

    if len(output) > 0:
        output = pd.DataFrame(output)
        output.to_csv(path_out, index=False)

    return


def calculate_sinr_lut(country, region, technology):
    """
    Calculate the sinr for each settlement tile.

    """
    folder = os.path.join(DATA_PROCESSED, country['iso3'],
        'regional_data', region['GID_{}'.format(country['lowest'])],
    )

    path_out = os.path.join(folder, '{}_sinr_lut.csv'.format(technology))

    if os.path.exists(path_out):
        return

    path_dist_lut = os.path.join(folder, '{}_distance_lut.csv'.format(technology))

    if not os.path.exists(path_dist_lut):
        return

    dist_lut = pd.read_csv(path_dist_lut)#[:10]

    output = []

    for idx, item in tqdm(dist_lut.iterrows(), total=dist_lut.shape[0]):

        dist1 = item['site1_distance_m']
        dist2 = item['site2_distance_m']
        dist3 = item['site3_distance_m']
        dist4 = item['site4_distance_m']

        sinr1 = get_sinr(params, dist1, dist2, dist3, dist4)
        sinr2 = get_sinr(params, dist2, dist3, dist4, dist1)
        if dist3 > 0:
            sinr3 = get_sinr(params, dist3, dist4, dist1, dist2)
        else:
            sinr3 = 0
        if dist4 > 0:
            sinr4 = get_sinr(params, dist4, dist1, dist2, dist3)
        else:
            sinr4 = 0

        output.append({
            # 'radio': item['radio'],
            # 'mcc': item['mcc'],
            # 'net': item['net'],
            # 'area': item['area'],
            # 'cell': item['cell'],
            # 'cell_lon': item['cell_lon'],
            # 'cell_lat': item['cell_lat'],
            'point_value': item['point_value'],
            'point_id': item['point_id'],
            'point_lon': item['point_lon'],
            'point_lat': item['point_lat'],
            'site1_distance_m': item['site1_distance_m'],
            'site1_id': item['site1_id'],
            # 'random_variation_mean': random_variation.mean(),
            # 'path_loss': path_loss,
            # 'antenna_gain': antenna_gain,
            # 'eirp': eirp,
            # 'losses': losses,
            # 'received_power': received_power,
            # 'interference': interference,
            # 'noise': noise,
            'sinr1': sinr1,
            'site2_id': item['site2_id'],
            'sinr2': sinr2,
            'site3_id': item['site3_id'],
            'sinr3': sinr3,
            'site4_id': item['site4_id'],
            'sinr4': sinr4,
        })

    output = pd.DataFrame(output)
    output.to_csv(path_out, index=False)

    return


def write_out_baseline_tile_coverage(country, technologies):
    """
    Write out site failures to .csv.

    """
    iso3 = country['iso3']

    filename = 'regional_data.csv'
    folder = os.path.join(DATA_PROCESSED, iso3)
    path = os.path.join(folder, filename)
    regional_data = pd.read_csv(path)#[:1]

    for technology in tqdm(technologies):

        # if not technology == 'NR':
        #     continue
        # print(technology)
        output = []

        filename = 'baseline_tile_coverage_{}.csv'.format(technology)
        folder_out = os.path.join(DATA_PROCESSED, iso3)
        if not os.path.exists(folder_out):
            os.mkdir(folder_out)
        path_output = os.path.join(folder_out, filename)

        # if os.path.exists(path_output):
        #     continue

        for idx, item in tqdm(regional_data.iterrows(), total=regional_data.shape[0]):

            gid_id = item['GID_id']

            if gid_id in ['MWI.13.1_1', 'MWI.20.1_1', 'MWI.26.1_1', 'MWI.6.2_1']:
                continue

            folder = os.path.join(DATA_PROCESSED, iso3, 'regional_data', gid_id, 'settlements')
            path_in = os.path.join(folder, 'tile_points.shp')

            if not os.path.exists(path_in):
                continue
            tile_points = gpd.read_file(path_in, crs='epsg:4326')
            tile_points = tile_points.to_crs(3857)

            filename = '{}_sinr_lut.csv'.format(technology)
            folder = os.path.join(DATA_PROCESSED, iso3, 'regional_data', gid_id)
            path_in = os.path.join(folder, filename)

            if not os.path.exists(path_in):
                continue

            sinr_lut = pd.read_csv(path_in)

            for idx, tile_point in tile_points.iterrows():

                point_id1 = '{}_{}'.format(
                        round(tile_point['geometry'].coords.xy[0][0],5),
                        round(tile_point['geometry'].coords.xy[1][0],5)
                    )

                sinr1 = -1
                covered = 0
                point_value = float(tile_point['value'])
                if point_value < 0:
                    point_value = 0

                for idx, tile in sinr_lut.iterrows():

                    point_id2 = '{}_{}'.format(
                        round(tile['point_lon'],5),
                        round(tile['point_lat'],5)
                    )

                    if point_id1 == point_id2:
                        if float(tile['sinr1']) > params['functioning_sinr']:
                            covered = 1
                            sinr1 = tile['sinr1']

                output.append({
                    'GID_0': item['GID_0'],
                    'GID_id': item['GID_id'],
                    'GID_level': item['GID_level'],
                    'population_km2': point_value,
                    'technology': technology,
                    'covered': covered,
                    'sinr1': sinr1,
                    'tile_point': point_id1,
                    'cell_point': point_id2
                })

        if not len(output) > 0:
            return

        output = pd.DataFrame(output)
        output.to_csv(path_output, index=False)

    return


def write_out_tile_coverage_layer(country, technologies):
    """
    Write out tile coverage layer to .shp.

    """
    iso3 = country['iso3']

    for technology in technologies:

        output = []

        filename = 'baseline_tile_coverage_{}.csv'.format(technology)
        folder = os.path.join(DATA_PROCESSED, iso3)
        path = os.path.join(folder, filename)
        if not os.path.exists(path):
            continue
        data = pd.read_csv(path)#[:1000]

        filename = 'baseline_tile_coverage_{}.shp'.format(technology)
        folder_out = os.path.join(DATA_PROCESSED, iso3, 'coverage')
        if not os.path.exists(folder_out):
            os.mkdir(folder_out)
        path_output = os.path.join(folder_out, filename)

        if os.path.exists(path_output):
            continue

        for idx, item in data.iterrows():
            # print(data)
            if item['covered'] == 1:
                # print(item)
                geom = Point([
                            float(item['tile_point'].split('_')[0]),
                            float(item['tile_point'].split('_')[1]),
                    ])

                geom = geom.buffer(500, cap_style = 3)

                output.append({
                    'type': 'Feature',
                    'geometry': geom,
                    'properties': {
                        'cell_point': item['cell_point'],
                        'pop_km2': item['population_km2'],
                        'covered': 1,
                    }
                })

        if not len(output) > 0:
            return
        # print(output)
        output = gpd.GeoDataFrame.from_features(output, crs='epsg:3857')

        # try:
        output = output.dissolve(by='covered')
        output = remove_small_holes(output)
        output = gpd.GeoDataFrame.from_features(output, crs='epsg:3857')
        # print(output)
        output.to_file(path_output, index=False)

    return


def remove_small_holes(output):
    """
    Remove small uncovered holes.

    """
    list_parts = []
    eps = 1000000

    for polygon in output['geometry'].values[0].geoms:

        list_interiors = []

        for interior in polygon.interiors:
            p = Polygon(interior)

            if p.area > eps:
                list_interiors.append(interior)

        temp_pol = Polygon(polygon.exterior.coords, holes=list_interiors)
        list_parts.append({
            'type': 'Polygon',
            'geometry': temp_pol,
            'properties':{}
        })

    return list_parts


def write_out_uncovered_layer(country, technologies):
    """
    Write out tile uncovered layer to .shp.

    """
    iso3 = country['iso3']

    for technology in technologies:

        # if not technology == 'LTE':
        #     continue

        filename = 'baseline_uncovered_{}.shp'.format(technology)
        folder_out = os.path.join(DATA_PROCESSED, iso3, 'coverage')
        if not os.path.exists(folder_out):
            os.mkdir(folder_out)
        path_output = os.path.join(folder_out, filename)

        # if os.path.exists(path_output):
        #     continue

        filename = 'baseline_tile_coverage_{}.shp'.format(technology)
        folder = os.path.join(DATA_PROCESSED, iso3, 'coverage')
        path = os.path.join(folder, filename)
        if not os.path.exists(path):
            continue
        covered = gpd.read_file(path, crs='epsg:3857')#[:1]
        covered['covered'] = 'Covered'
        covered = covered[['geometry', 'covered']]

        filename = 'national_outline.shp'
        folder = os.path.join(DATA_PROCESSED, iso3)
        path = os.path.join(folder, filename)
        if not os.path.exists(path):
            continue
        outline = gpd.read_file(path, crs='epsg:4326')#[:1]
        outline = outline.to_crs(3857)
        outline = outline[['geometry']]

        output = gpd.overlay(covered, outline, how='symmetric_difference') #
        output['covered'] = 'Uncovered'

        output = pd.concat([output, covered])

        if not len(output) > 0:
            return

        output.to_file(path_output, index=False)

    return


def write_out_baseline_coverage(country, scenarios, technologies):
    """
    Write out site failures to .csv.

    """
    iso3 = country['iso3']
    # name = country['country']
    # regional_level = country['gid_region']

    filename = 'baseline_coverage.csv'
    folder_out = os.path.join(DATA_PROCESSED, iso3)
    if not os.path.exists(folder_out):
        os.mkdir(folder_out)
    path_output = os.path.join(folder_out, filename)

    # if os.path.exists(path_output):
    #     return

    filename = 'regional_data.csv'
    folder = os.path.join(DATA_PROCESSED, iso3)
    path = os.path.join(folder, filename)
    regional_data = pd.read_csv(path)#[:1]

    output = []

    for technology in technologies:

        for idx, item in regional_data.iterrows():

            gid_id = item['GID_id']
            area_km2 = item['area_km2']
            population_total = item['population_total']

            filename = '{}_sinr_lut.csv'.format(technology)
            folder = os.path.join(DATA_PROCESSED, iso3, 'regional_data', gid_id)
            path_in = os.path.join(folder, filename)

            if not os.path.exists(path_in):
                continue

            sinr_lut = gpd.read_file(path_in, crs='epsg:4326')

            covered_population = 0

            for idx, tile in sinr_lut.iterrows():
                if float(tile['point_value']) > 0:
                    if float(tile['sinr1']) > params['functioning_sinr']:
                        covered_population += float(tile['point_value'])
            try:
                covered_pop_perc = round((covered_population / item['population_total'])*100)
            except:
                print('problem with {}, {}'.format(covered_population, item['population_total']))
                covered_pop_perc = 0

            output.append({
                'GID_0': item['GID_0'],
                'GID_id': item['GID_id'],
                'GID_level': item['GID_level'],
                'population_total': item['population_total'],
                'area_km2': area_km2,
                'population_km2': population_total / area_km2,
                'technology': technology,
                'covered_pop': covered_population,
                'covered_pop_perc': covered_pop_perc,
                'uncovered_pop': item['population_total'] - covered_population,
                'uncovered_pop_perc': round((
                    (item['population_total'] - covered_population) /
                    item['population_total'])*100),
            })

    if not len(output) > 0:
        return

    output = pd.DataFrame(output)
    output.to_csv(path_output, index=False)

    return


if __name__ == '__main__':

    crs = 'epsg:4326'
    os.environ['GDAL_DATA'] = ("C:\\Users\edwar\\Anaconda3\\Library\\share\\gdal")
    random.seed(params['seed_value'])

    countries = get_countries()

    for idx, country in countries.iterrows():

        if not country['iso3'] == 'MWI':
            continue

        create_national_sites_layer(country)

        process_country_shapes(country)

        process_regions(country)

        process_settlement_layer(country)

        scenarios  = get_scenarios()

        regions = get_regions(country, country['lowest'])#[:6]

        get_regional_data(country, regions)

        # for idx, region in tqdm(regions.iterrows(), total=regions.shape[0]):

        #     GID_level = 'GID_{}'.format(country['lowest'])
        #     gid_id = region[GID_level]

        #     # if not gid_id == 'MWI.11.14_1': #'MWI.1.1_1': #'GHA.9.7_1': #:#: #'GHA.1.12_1':
        #     #     continue
        #     print('Working on {}'.format(gid_id))
        #     process_regional_sites_layer(country, region)

        #     process_tech_specific_sites(country, region, technologies)

        #     # cut_surface_water_layers(country, region)

        #     cut_settlement_layers(country, region) # Cut settlement layers by region

        #     convert_to_shapes(country, region) # Convert settlement layers to points

        #     write_as_text(country, region) # Write out points as .csv

        #     for technology in tqdm(technologies):

        #         # if not technology == 'GSM':
        #         #     continue

        #         folder_out = os.path.join(DATA_PROCESSED, country['iso3'], 'regional_data', gid_id)

        #         if not os.path.exists(folder_out):
        #             os.makedirs(folder_out)

        #         calculate_distances_lut(country, region, technology)

        #         calculate_sinr_lut(country, region, technology)

        write_out_baseline_tile_coverage(country, technologies)

        write_out_tile_coverage_layer(country, technologies)

        write_out_uncovered_layer(country, technologies)

        write_out_baseline_coverage(country, scenarios, technologies)
