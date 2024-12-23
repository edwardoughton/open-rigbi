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
from misc import process_country_shapes, process_regions #, get_scenarios, get_tropical_scenarios

import math
import os
from typing import Optional

import geopandas as gpd
import pandas as pd
import numpy as np
import pyproj
from shapely import Point
import snail
from tqdm import tqdm

class FloodRisk:
    def __init__(self, iso2, iso3):
        self.iso2 = iso2
        self.iso3 = iso3

    def create_buffers(telecom_points: gpd.GeoDataFrame, buffer_distance_km: float) -> Optional[gpd.GeoDataFrame]:
        """
        Create buffers around telecom points.

        Args:
            telecom_points (gpd.GeoDataFrame): GeoDataFrame containing telecom points.
            buffer_distance_km (float): Buffer distance in kilometers.

        Returns:
            Optional[gpd.GeoDataFrame]: GeoDataFrame containing buffer polygons or None if no points are provided.
        """
        print("Creating buffers around telecom points...")
        if not telecom_points.empty:
            geod = pyproj.Geod(ellps="WGS84")
            
            buffer_distance_m = buffer_distance_km * 1000
            
            buffers = []
            for _, row in telecom_points.iterrows():
                lon, lat = row['geometry'].x, row['geometry'].y

                # Use a geod to calculate the new lon and lat values and append to buffers list
                lon_buffer, lat_buffer, _ = geod.fwd(lon, lat, 0, buffer_distance_m)
                buffer_geom = Point(lon_buffer, lat_buffer).buffer(buffer_distance_m)
                buffers.append(buffer_geom)
            
            buffers_gdf = gpd.GeoDataFrame(geometry=buffers)
            buffers_gdf.set_crs('EPSG:4326', inplace=True)
            print("Buffers around telecom points created successfully.")
            return buffers_gdf
        else:
            print("No telecom points provided.")
            return None

    def preprocess(self, code):
        county_list = []
        df = pd.read_csv(f"../{BASE_PATH}/countries.csv", encoding='latin-1')
        level = df.loc[df['iso3'] == self.iso3, 'gid_region'].values[0]
        process_country_shapes(self.iso3)
        process_regions(self.iso3, level)
        if not os.path.exists(f"{DATA_PROCESSED}/{self.iso3.upper()}") and not os.path.isdir(f"{DATA_PROCESSED}/{self.iso3.upper()}/regions"):
            os.makedirs(f"{DATA_PROCESSED}/{self.iso3.upper()}/regions")
            print(f"Created directory {DATA_PROCESSED}/{self.iso3.upper()}")
        else:
            print(f"Directory {DATA_PROCESSED}/{self.iso3.upper()} already exists")

        path = f"./{DATA_PROCESSED}/{self.iso3.upper()}/regions"
        mcc_data = {}  # Dictionary to store GeoDataFrames for each MCC code
        total_rows = sum(1 for _ in open("/home/cisc/projects/open-rigbi/scripts/FloodRisk/data/cell_towers_2022-12-24.csv")) - 1  # Subtract 1 for the header row
        chunksize = 1000
        output_path = f"{path}/processed_cell_towers_{self.iso3.upper()}_{code}.shp"
        if os.path.exists(output_path):
            print(f"{output_path} already exists")

        features = []

        for chunk in tqdm(pd.read_csv(f"/home/cisc/projects/open-rigbi/scripts/FloodRisk/data/cell_towers_2022-12-24.csv", chunksize=1000)):
            #  Filter rows by the current MCC code and LTE radio type
            filtered_chunk = chunk[chunk['mcc'] == code]
            if filtered_chunk.empty:
                continue
    
            new_filtered_chunk = filtered_chunk[filtered_chunk['radio'] == 'LTE']
    
            if not new_filtered_chunk.empty:
                new_filtered_chunk['geometry'] = [Point(row.lon, row.lat) for row in new_filtered_chunk.itertuples()]
                gdf_chunk = gpd.GeoDataFrame(new_filtered_chunk, geometry='geometry')
                features.append(gdf_chunk)
            else:
                continue

        if features:  # If there are features for the current MCC code
            if int(level) == 0:
                all_features = pd.concat(features, ignore_index=True)
                all_features.to_file(f"{path}/processed_cell_towers_{self.iso3.upper()}_{code}.shp")
                print(f"Saved {code} data to {output_path}")
                gid = gpd.read_file(f"/home/cisc/projects/open-rigbi/scripts/FloodRisk/data/processed/{self.iso3}/regions/regions_{level}_{self.iso3}.shp")
                all_features = gpd.sjoin(all_features, gid, how="inner", op="intersects")
                print(all_features.columns)
                return all_features
            else:
                for idx, f in enumerate(features):
                    f.to_file(f"{path}/processed_cell_towers_{self.iso3.upper()}_{code}_{idx}.shp")
                    print(f"Saved {code}, {idx} data to {output_path}")
                    gid = gpd.read_file(f"/home/cisc/projects/open-rigbi/scripts/FloodRisk/data/processed/{self.iso3}/regions/regions_{level}_{self.iso3}.shp")
                    f = gpd.sjoin(f, gid, how="inner", op="intersects")
                    print(f.columns)
                    return pd.concat(f, ignore_index=True)
        # return mcc_data

    def get_stations(self, telecom_features):
        self.convert_to_stations(telecom_features)
        telecom_features = telecom_features.dropna(subset=['bs_id_int'])
        telecom_features = telecom_features[telecom_features['bs_id_int'] != 0]

        if telecom_features is not None:
            print(f"Number of telecom points before buffering: {len(telecom_features)}")  # Debug print

            buffer_distance_km = self.buffer_distance
            telecom_buffers = self.create_buffers(telecom_features, buffer_distance_km)
            if telecom_buffers is not None:
                print(f"Number of buffered telecom points: {len(telecom_buffers)}")  # Debug print

                self.save_as_shapefile(telecom_buffers, f"telecom_buffers_{self.iso2}.shp")
                print(f"Number of telecom points after saving shapefile: {len(telecom_features)}")  # Debug print 
    
    global all_new_lengths
    all_new_lengths = []
    @staticmethod
    def convert_to_stations(data):
        data['bs_id_float'] = data['cell'] / 256
        data['bs_id_int'] = np.round(data['bs_id_float'], 0)
        data['sector_id'] = data['bs_id_float'] - data['bs_id_int']
        data['sector_id'] = np.round(data['sector_id'].abs() * 256)

        data = data.drop_duplicates(subset=['bs_id_int', 'sector_id'])
        return data

    def process(self, telecom_features, scenario_path, feature_name, scenario_name) -> None:
        """ 
        Download, prepare, and intersect flood data with a given regional layer.

        Note:
            This code is mostly adapted from code provided by Mr. Tom Russel from Oxford University.
        """
        
        self.convert_to_stations(telecom_features)
        telecom_features = telecom_features.dropna(subset=['bs_id_int'])
        telecom_features = telecom_features[telecom_features['bs_id_int'] != 0]
        if not os.path.exists(f"/home/cisc/projects/open-rigbi/scripts/FloodRisk/data/exports/{self.iso3}"):
            os.makedirs(f"/home/cisc/projects/open-rigbi/scripts/FloodRisk/data/exports/{self.iso3}")
        telecom_features.to_csv(f"/home/cisc/projects/open-rigbi/scripts/FloodRisk/data/exports/{self.iso3}/towers_{self.iso3}.csv", index=False)
        return telecom_features

        # scen = get_scenarios()
        # trop_scen = get_tropical_scenarios()

        """if telecom_features is not None:
            print(f"Number of telecom points before buffering: {len(telecom_features)}")  # Debug print

            buffer_distance_km = self.buffer_distance
            telecom_buffers = self.create_buffers(telecom_features, buffer_distance_km)
            
            if telecom_buffers is not None:
                print(f"Number of buffered telecom points: {len(telecom_buffers)}")  # Debug print

                self.save_as_shapefile(telecom_buffers, f"telecom_buffers_{self.iso2}.shp")
                print(f"Number of telecom points after saving shapefile: {len(telecom_features)}")  # Debug print 

                flood_path = scenario_path
                grid, _ = snail.io.read_raster_metadata(flood_path)
                prepared = snail.intersection.prepare_points(telecom_features)
                flood_intersections = snail.intersection.split_points(prepared, grid)

                flood_intersections = snail.intersection.apply_indices(flood_intersections, grid)
                flood_data = snail.io.read_raster_band_data(flood_path)
                flood_intersections["inun"] = snail.intersection.get_raster_values_for_splits(
                    flood_intersections, flood_data
                )

                # Debug printing
                flood_intersections = flood_intersections[['inun', 'bs_id_int', 'sector_id', 'geometry']]
                print(flood_intersections.tail(5))
                print(flood_intersections.columns)
                print(len(flood_intersections))

                # Ensure the directory exists
                output_dir = os.path.join(
                    "/home/cisc/projects/open-rigbi/scripts/FloodRisk/data/exports", 
                    self.iso3, 
                    feature_name
                )
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                    
                # Save as GeoDataFrame
                output_path = os.path.join(
                    output_dir, 
                    f"telecom_with_flood_{self.iso2}_{feature_name}_{scenario_name}.csv"
                )
                gpd.GeoDataFrame.to_file(flood_intersections, output_path)

                print(f"Telecom features with flood intersections saved as CSV: {output_path}")
            else:
                print("No buffers created around telecom points.")
        else:
            print("No telecom features found for the provided country code.")
"""
