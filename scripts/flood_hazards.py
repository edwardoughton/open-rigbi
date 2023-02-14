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







if __name__ == "__main__":

    os.environ['GDAL_DATA'] = ("C:\\Users\\edwar\\Anaconda3\\Library\\share\\gdal")

    countries = get_countries()
    scenarios = get_scenarios()

    # failures = []

    for idx, country in countries.iterrows():

        #if not country['iso3'] in ['USA',#'ARG',
        #    #'BEL','BIH','BRB','EST','GUM','KHM','LSO','TWN','VGB', 'AND',
        #    #'BFA','UBZ','BMU','BTN','CYM','DJI','FRO','ISR','KNA','LCA','MLI','MNG','MUS','PRY','TCA','WSM'
        #    ]: #'GHA'
        #    continue
        #print(country)
        if not country['iso3'] in [
            'ASM','AUS','COK','FJI','FSM','GUM','KIR','MHL','MNP',
            'NCL','NFK','NIU','NRU','NZL','PCN','PLW','PNG','PYF',
            'SLB','TKL','TON','TUV','UMI','VUT','WLF','WSM',
            ]:
            continue



        print('-Working on {}'.format(country['iso3']))

        #process_flooding_layers(country, scenarios)


        regions = get_regions(country, country['gid_region'])#[::-1]
        if len(regions) == 0:
            continue

        for idx, region in regions.iterrows():


            region = region['GID_{}'.format(country['gid_region'])]
            #if not 'USA.2.1_1' in region: #'USA.10.43_1' in region:# or not 'USA.51.' in region:
            #    continue

            print('processing : {}'.format(region))
            process_regional_flooding_layers(country, region, scenarios)
            process_flooding_extent_stats(country, region, scenarios)
     #print(failures)
