"""
Generate country regional codes to pass to each node.

Written by Ed Oughton.

August 2022.

"""
import os
import sys
import configparser
# import pandas as pd
# import numpy as np
# import geopandas as gpd
import random

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

sys.path.insert(1, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from misc import get_scenarios

DATA_RAW = os.path.join(BASE_PATH, 'raw')
DATA_PROCESSED = os.path.join(BASE_PATH, 'processed')


if __name__ == "__main__":

    scenarios = get_scenarios()
   
    scenarios = [os.path.basename(i)[:-4] for i in scenarios]#[:12] 
    #scenarios = [i for i in scenarios if 'GFDL' in i][:8]
    #print(scenarios)
    #random.shuffle(scenarios)

    scenarios = [i.replace('.tif','') for i in scenarios]

    print(*scenarios, sep='\n')
