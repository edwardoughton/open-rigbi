import geopandas as gpd
import pandas as pd
import rasterio
import os
from tqdm import tqdm
import json
from rasterio.mask import mask
from joblib import Parallel, delayed

def create_buffers(gdf, buffer_size):
    gdf['geometry'] = gdf['geometry'].apply(lambda geom: geom.buffer(buffer_size))
    return gdf
    

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
        return print('Completed settlement layer processing')

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
    mobile_codes = pd.read_csv(f"../{BASE_PATH}/mobile_codes.csv", encoding='latin1')
    mobile_codes = mobile_codes.drop_duplicates(subset=['mcc'])
    df = pd.read_csv(f"../{BASE_PATH}/countries.csv", encoding='latin-1')
    df = df[df['Exclude'] != 1]
    print("Loaded data")
    
    error = []
    def process_country(country_code, country_csv):
        country_regions = []
        try:
            level = df.loc[df['iso3'] == country_code, 'gid_region'].values[0]
            level = int(level)
            country_code_2 = df[df['iso3'] == country_code]['iso2'].values[0]
            mcc = mobile_codes[mobile_codes['iso3'] == country_code]['mcc'].values[0]
            # print(f"Processing Country code: {country_code}")
            country = country_csv[country_csv['iso3'] == country_code]
            country = country.to_records('dicts')[0]
            print(f"Processing Country code: {country_code}")
            process_settlement_layer(country)

        except Exception as e:
            print(f"Error processing country code {country_code}: {e}")
            error.append(country_code)
            return country_code, pd.DataFrame()
        
    results = Parallel(n_jobs=-1)(delayed(process_country)(country_code, df) for country_code in df['iso3'])
    process_settlement_layer(country)
    
    

