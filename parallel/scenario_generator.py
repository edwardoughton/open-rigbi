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
from misc import get_scenarios, get_tropical_storm_scenarios

DATA_RAW = os.path.join(BASE_PATH, 'raw')
DATA_PROCESSED = os.path.join(BASE_PATH, 'processed')


if __name__ == "__main__":

    scenarios = []
    # scenarios = get_scenarios()
    # scenarios = [os.path.basename(i).replace('.tif','') for i in scenarios]
    scenarios_tropical = get_tropical_storm_scenarios()
    # scenarios_tropical = [os.path.basename(i).replace('.tif','') for i in scenarios_tropical]#[:12] 
    # scenarios = [i for i in scenarios if 'coastal' in i]#[:8]
    # print(scenarios)
    #random.shuffle(scenarios)
    #scenarios = [i.replace('.tif','') for i in scenarios]

    scenarios = scenarios + scenarios_tropical

    #scenarios = [
    #'STORM_FIXED_RETURN_PERIODS_CNRM-CM6-1-HR_10000_YR_RP',
    #'STORM_FIXED_RETURN_PERIODS_CNRM-CM6-1-HR_1000_YR_RP',
    #'STORM_FIXED_RETURN_PERIODS_EC-Earth3P-HR_500_YR_RP',
    #'STORM_FIXED_RETURN_PERIODS_HadGEM3-GC31-HM_500_YR_RP',
    #'STORM_FIXED_RETURN_PERIODS_constant_1000_YR_RP',
    #'STORM_FIXED_RETURN_PERIODS_CMCC-CM2-VHR4_50_YR_RP',
    #'STORM_FIXED_RETURN_PERIODS_EC-Earth3P-HR_10000_YR_RP'
    #]

    print(*scenarios, sep='\n')
