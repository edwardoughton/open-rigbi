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

import numpy as np
import geopandas as gpd
import pandas as pd
from shapely import Point

class FloodRisk:
    def __init__(self, iso3):
        self.iso3 = iso3

    def preprocess(self, *codes):
        if not os.path.exists(f"{DATA_PROCESSED}/{self.iso3.upper()}") and not os.path.isdir(f"{DATA_PROCESSED}/{self.iso3.upper()}/regions"):
            os.makedirs(f"{DATA_PROCESSED}/{self.iso3.upper()}/regions")
            print(f"Created directory {DATA_PROCESSED}/{self.iso3.upper()}")
        else:
            print(f"Directory {DATA_PROCESSED}/{self.iso3.upper()} already exists")

        path = Path(DATA_PROCESSED / f"{self.iso3.upper()}/regions")
        mcc_data = {}  # Dictionary to store GeoDataFrames for each MCC code
        total_rows = sum(1 for _ in open(f"{DATA_RAW}/cell_towers_2022-12-24.csv")) - 1  # Subtract 1 for the header row
        chunksize = 1000

        for code in codes:  # Loop over each MCC code
            output_path = Path(path / f"processed_cell_towers_{self.iso3.upper()}_{code}.shp")
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
                all_features.to_file(output_path)
                print(f"Saved {code} data to {output_path}")
                mcc_data[code] = all_features  # Store the GeoDataFrame in the dictionary

        return mcc_data

all_new_lengths = []
def convert_to_stations(data_dict):
    for country_code, data in data_dict.items():
        print(f"Processing {country_code}")
        print(data.head(10))

        data['bs_id_float'] = data['cell'] / 256
        data['bs_id_int'] = np.round(data['bs_id_float'], 0)
        data['sector_id'] = data['bs_id_float'] - data['bs_id_int']
        data['sector_id'] = np.round(data['sector_id'].abs() * 256)

        unique_bs_id_int = data['bs_id_int'].drop_duplicates()
        unique_sector_id_int = data['sector_id'].drop_duplicates()

        new_lengths = {
            'Country': country_code,
            'Unique 4G Stations': len(data),
            'Unique BS ID Int': len(unique_bs_id_int),
            'Unique Sector ID Int': len(unique_sector_id_int)
        }
        all_new_lengths.append(new_lengths)

    global all_new_lengths
    return all_new_lengths