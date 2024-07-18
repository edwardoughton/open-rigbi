#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# preprocess.py file for OpenRigbi, designed to visalize risk to telecom
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

import math
import os

import geopandas as gpd
import pandas as pd
from shapely import Point

class FloodRisk:
    def __init__(self, iso2, iso3):
        self.iso2 = iso2
        self.iso3 = iso3

    def preprocess(self, *codes):
        county_list = []
        if not os.path.exists(f"{DATA_PROCESSED}/{self.iso3.upper()}") and not os.path.isdir(f"{DATA_PROCESSED}/{self.iso3.upper()}/regions"):
            os.makedirs(f"{DATA_PROCESSED}/{self.iso3.upper()}/regions")
            print(f"Created directory {DATA_PROCESSED}/{self.iso3.upper()}")
        else:
            print(f"Directory {DATA_PROCESSED}/{self.iso3.upper()} already exists")

        path = f"./{DATA_PROCESSED}/{self.iso3.upper()}/regions"
        mcc_data = {}  # Dictionary to store GeoDataFrames for each MCC code
        total_rows = sum(1 for _ in open(f"{DATA_RAW}/cell_towers_2022-12-24.csv")) - 1  # Subtract 1 for the header row
        chunksize = 1000

        for code in codes:  # Loop over each MCC code
            output_path = f"{path}/processed_cell_towers_{self.iso3.upper()}_{code}.shp"
            if os.path.exists(output_path):
                print(f"{output_path} already exists")
                continue
            features = []
            chunk_count = 0
            total_chunks = math.ceil(total_rows / chunksize)

            for chunk in pd.read_csv(f"{DATA_RAW}/cell_towers_2022-12-24.csv", chunksize=1000):
                #  Filter rows by the current MCC code and LTE radio type
                filtered_chunk = chunk[chunk['mcc'] == code]
                new_filtered_chunk = filtered_chunk[filtered_chunk['radio'] == 'LTE']
                if not new_filtered_chunk.empty:
                    new_filtered_chunk['geometry'] = [Point(row.lon, row.lat) for row in new_filtered_chunk.itertuples()]
                    gdf_chunk = gpd.GeoDataFrame(new_filtered_chunk, geometry='geometry')
                    features.append(gdf_chunk)
                    chunk_count += 1
                    print(f"Processed chunk {chunk_count}/{total_chunks} for MCC {code}")

            if features:  # If there are features for the current MCC code
                all_features = pd.concat(features, ignore_index=True)
                print(f"Saved {code} data to {output_path}")
                gid = gpd.read_file(f"./{DATA_RAW}/NLD/regions/regions_2_NLD.shp")
                gid = gid.to_crs("EPSG:4326")
                all_features = gpd.sjoin(all_features, gid, how="inner", op="intersects")
                county_list = all_features['NAME_2'].drop_duplicates().to_list()
                for county in county_list:
                    county_df = all_features[all_features['NAME_2'] == county]
                    county_df.to_file(f"{path}/processed_cell_towers_county_{county}.shp")
                mcc_data[code] = all_features  # Store the GeoDataFrame in the dictionary
                        
        return mcc_data