import geopandas as gpd
import pandas as pd
import rasterio
import os
import glob
from constants import *
from rasterio.mask import mask
import json

def create_buffers(gdf, buffer_size):
    gdf['geometry'] = gdf['geometry'].apply(lambda geom: geom.buffer(buffer_size))
    return gdf
    

def process_pop(iso3, gid_level):
    # path_settlements = os.path.join(DATA_RAW,'settlement_layer','ppp_2020_1km_Aggregated.tif')
    path_settlements = "/home/cisc/projects/open-rigbi/scripts/FloodRisk/data/settlement_layer/ppp_2020_1km_Aggregated.tif"
    print(f"Processing population data for {iso3} at GID level {gid_level}")

    settlements = rasterio.open(path_settlements, 'r+')
    settlements.nodata = 255
    settlements.crs.from_epsg(4326)

    return

def process_age_sex_structure(country):
    """
    Clip each demographic layer to the chosen country boundary
    and place in desired country folder.

    Parameters
    ----------
    country : dict
        Contains all desired country information.

    """
    iso3 = country['iso3']

    path = os.path.join(DATA_RAW, 'settlement_layer')
    all_paths = glob.glob(path + '/*.tif')

    for path in all_paths:

        # if os.path.basename(path).startswith('ppp_2020_1km_Aggregated'):
        #     continue

        directory_out = os.path.join(DATA_PROCESSED, iso3, 'age_sex_structure')

        if not os.path.exists(directory_out):
            os.makedirs(directory_out)

        filename = os.path.basename(path)
        path_out = os.path.join(directory_out, filename)

        if os.path.exists(path_out):
            continue

        settlements = rasterio.open(path, 'r+')
        settlements.nodata = 0
        settlements.crs = {"init": "epsg:4326"}

        filename = 'national_outline.shp'
        path_country = os.path.join(DATA_PROCESSED, iso3, filename)

        if os.path.exists(path_country):
            country = gpd.read_file(path_country)
        else:
            print('Must generate national_outline.shp first')

        geo = gpd.GeoDataFrame({'geometry': country['geometry']})

        coords = [json.loads(geo.to_json())['features'][0]['geometry']]

        #chop on coords
        out_img, out_transform = mask(settlements, coords, crop=True)

        # Copy the metadata
        out_meta = settlements.meta.copy()

        out_meta.update({"driver": "GTiff",
                        "height": out_img.shape[1],
                        "width": out_img.shape[2],
                        "transform": out_transform,
                        "crs": 'epsg:4326'})

        with rasterio.open(path_out, "w", **out_meta) as dest:
                dest.write(out_img)

    return #print('Completed processing of settlement layer')

def create_union(*gdf):
    return gdf.unary_union(*gdf)

if __name__ == "__main__":
    pass