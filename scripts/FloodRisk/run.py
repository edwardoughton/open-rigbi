#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# run.py file for OpenRigbi, designed to visualize risk to telecom
# infrastructure due to natural disasters
#
# SPDX-FileCopyrightText: 2024 Aryaman Rajaputra <arajaput@gmu.edu>
# SPDX-License-Identifier: MIT
#
# Note: The programs and configurations used by this script may not be under the same license.
# Please check the LICENSING file in the root directory of this repository for more information.
#
# This script was created by Aryaman Rajaputra
from constants import *
from preprocess import FloodRisk
from process import GID

import geopandas as gpd
import pandas as pd

import os

if __name__ == "__main__":
    mobile_codes = pd.read_csv(f"../{BASE_PATH}/mobile_codes.csv", encoding='latin1').drop_duplicates(subset=['mcc'], keep='first')
    df = pd.read_csv(f"../{BASE_PATH}/countries.csv", encoding='latin-1')
    for country in df['iso3']:
        country_code = country
        country_code_2 = df.loc[df['iso3'] == country, 'iso2'].values[0]
        mcc = mobile_codes[mobile_codes['mcc'] == country_code]
        print("Country code entered:", country_code)
        fr = FloodRisk(country_code_2, country_code)
        _ = fr.preprocess(mcc)
        g = GID(country_code_2, country_code)
        for feature in os.listdir(f"./{DATA_PROCESSED}/{country_code.upper()}/regions"):
            if feature.endswith(".shp"):
                feature_name = Path(feature).stem
                feature = gpd.read_file(f"./{DATA_PROCESSED}/{country_code.upper()}/regions/{feature}")
                dir_list = os.listdir(f"./{DATA_FOLDER}/flood_layer/{country_code.lower()}/wri_aqueduct_version_2")[:30]
                for scenario in dir_list:
                    scenario_path = f"./{DATA_FOLDER}/flood_layer/{country_code.lower()}/wri_aqueduct_version_2/{scenario}"
                    scenario_name = Path(scenario).stem
                    g.process(feature, scenario_path, feature_name, scenario_name)
