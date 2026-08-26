"""
Create coastal lookup table. 

Written by Ed Oughton. 

September 2023

"""
import os
import configparser
import pandas
import geopandas as gpd
from tqdm import tqdm

from misc import get_countries

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']
DATA_RAW = os.path.join(BASE_PATH, 'raw')


def read_valid_layer(path, target_crs, default_crs=None):
    """Read, project, and repair a vector layer before spatial operations."""
    layer = gpd.read_file(path)
    if layer.crs is None:
        if default_crs is None:
            raise ValueError(f"Layer has no CRS metadata: {path}")
        layer = layer.set_crs(default_crs)
    layer = layer.to_crs(target_crs)
    layer = layer[layer.geometry.notna() & ~layer.geometry.is_empty].copy()
    layer.geometry = layer.geometry.make_valid()
    layer = layer[layer.geometry.notna() & ~layer.geometry.is_empty].copy()
    return layer


def process_coastal_lut(country):
    """
    Meta function to process coastal lookup table. 

    """

    process_coastal_shapefile()

    process_country_coast(country)

    process_regional_lut(country)

    return


def process_coastal_shapefile():
    """
    Process the global coastal shapefile. 
    
    """
    filename = 'global_coastal_buffer.shp'
    folder_out = os.path.join(BASE_PATH, 'processed', 'coastal')
    if not os.path.exists(folder_out):
        os.mkdir(folder_out)
    path_coastal = os.path.join(folder_out, filename)

    if not os.path.exists(path_coastal):

        filename = 'GSHHS_l_L1.shp'
        path = os.path.join(DATA_RAW, 'gshhg-shp-2.3.7', 'GSHHS_shp', 'l', filename)
        gdf_coastal = read_valid_layer(
            path, target_crs='epsg:3857', default_crs='epsg:4326'
        )

        gdf_coastal['geometry'] = gdf_coastal['geometry'].boundary

        gdf_coastal['geometry'] = gdf_coastal['geometry'].buffer(5000)
        gdf_coastal['geometry'] = gdf_coastal['geometry'].make_valid()

        gdf_coastal.to_file(path_coastal)

    return


def process_country_coast(country):
    """
    Export coastal outline per country.
    
    """
    iso3 = country["iso3"]

    filename = 'national_coastal_regions.shp'
    folder_out = os.path.join(BASE_PATH, 'processed', iso3, 'coastal')
    if not os.path.exists(folder_out):
        os.makedirs(folder_out)
    path_out = os.path.join(folder_out, filename)
    if os.path.exists(path_out):
        return

    filename = 'global_coastal_buffer.shp'
    folder = os.path.join(BASE_PATH, 'processed', 'coastal')
    path = os.path.join(folder, filename)
    gdf_coastal = read_valid_layer(
        path, target_crs='epsg:3857', default_crs='epsg:3857'
    )

    filename = "national_outline.gpkg"
    folder = os.path.join('data', 'processed', iso3)
    path = os.path.join(folder, filename)
    if not os.path.exists(path):
        return print(f"Could not find path {path}")
    country_outline = read_valid_layer(
        path, target_crs='epsg:3857', default_crs='epsg:4326'
    )

    output = gpd.overlay(gdf_coastal, country_outline, how='intersection')
    output['geometry'] = output['geometry'].make_valid()
    output = output[output.geometry.notna() & ~output.geometry.is_empty].copy()
    
    if len(output) == 0:
        return

    output.to_file(path_out)
    

def process_regional_lut(country):
    """
    Export regional lookup for coastline areas. 
    
    """
    iso3 = country["iso3"]
    gid_region = int(country['gid_region'])
    gid_level = 'GID_{}'.format(gid_region)
        
    filename = 'coastal_lookup.csv'
    folder_out = os.path.join(BASE_PATH, 'processed', iso3, 'coastal')
    if not os.path.exists(folder_out):
        os.makedirs(folder_out)
    path_out = os.path.join(folder_out, filename)

    if os.path.exists(path_out):
        return

    filename = 'national_coastal_regions.shp'
    folder = os.path.join(BASE_PATH, 'processed', iso3, 'coastal')
    path = os.path.join(folder, filename)
    if not os.path.exists(path):
        return
    gdf_coastal = read_valid_layer(
        path, target_crs='epsg:3857', default_crs='epsg:3857'
    )
    coast_dict = gdf_coastal.to_dict("records")

    #loading in regions by GID level
    filename = "regions_{}_{}.gpkg".format(gid_region, iso3)
    path_region = os.path.join('data', 'processed', iso3, 'regions', filename)
    gdf_region = read_valid_layer(
        path_region, target_crs='epsg:3857', default_crs='epsg:4326'
    )
    region_dict = gdf_region.to_dict('records')
    
    my_shp = []
    my_csv = []

    for region in region_dict:

        if region['geometry'] == None:
            continue

        for coast in coast_dict:

            if region['geometry'].intersects(coast['geometry']):

                    my_shp.append({
                        'geometry': region['geometry'],
                        'properties': {
                            'gid_id': region[gid_level],
                            'gid_level': gid_level,
                        }
                    })
                    my_csv.append({
                        'gid_id': region[gid_level],
                        'gid_level': gid_level,
                    })

    if len(my_csv) == 0:
        return  
    
    output = pandas.DataFrame(my_csv)
    output = output.drop_duplicates()

    output.to_csv(path_out, index= False) 


if __name__ == "__main__":

    countries = get_countries()

    print('Working on process_coastal_shapefile')
    process_coastal_shapefile()

    for country in countries:

        # if not country['iso3'] == 'CYP':
        #     continue

        print("---- {}".format(country['iso3']))

        print('Working on process_country_coast')
        process_country_coast(country)

        print('Working on process_regional_lut')
        process_regional_lut(country)
