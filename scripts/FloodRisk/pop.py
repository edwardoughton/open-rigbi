import geopandas as gpd
import pandas as pd
import rasterio
import os
from tqdm import tqdm
import json
from rasterio.mask import mask

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
    print(settlements)
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
    regional_level = country['gid_region']

    path_settlements = "/home/cisc/projects/open-rigbi/scripts/FloodRisk/data/settlement_layer/ppp_2020_1km_Aggregated.tif"
    print(f"Processing population data for {iso3} at GID level {regional_level}")

    settlements = rasterio.open(path_settlements, 'r+')
    settlements.nodata = 255
    settlements.crs.from_epsg(4326)

    iso3 = country['iso3']
    # path_country = os.path.join(DATA_PROCESSED, iso3,
    #     'national_outline.shp')
    path_country = f"/home/cisc/projects/open-rigbi/data/processed/{iso3}/national_outline.shp"

    if os.path.exists(path_country):
        country = gpd.read_file(path_country)
    else:
        print('Must generate national_outline.shp first' )

    # path_country = os.path.join(DATA_PROCESSED, iso3)
    path_country = f"/home/cisc/projects/open-rigbi/data/processed/{iso3}"
    shape_path = os.path.join(path_country, 'settlements.tif')

    if os.path.exists(shape_path):
        return  print('Completed settlement layer processing')

    print('----')
    print('Working on {} level {}'.format(iso3, regional_level))

    bbox = country.envelope
    geo = gpd.GeoDataFrame()

    geo = gpd.GeoDataFrame({'geometry': bbox})

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

    return print('Completed processing of settlement layer')


if __name__ == "__main__":
    df = pd.read_csv(f"/home/cisc/projects/open-rigbi/data/countries.csv", encoding='latin-1')
    df = df[df['Exclude'] != 1]
    country_csv = df[df['iso3'] == 'NLD']
    process_settlement_layer(country_csv.to_records('dicts')[0])