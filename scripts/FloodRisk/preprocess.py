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
from misc import process_country_shapes, process_regions, get_scenarios
import math
import os
from typing import Optional

import geopandas as gpd
import pandas as pd
import numpy as np
import pyproj
from shapely import Point
import snail
import rasterio
from rasterio.mask import mask
from tqdm import tqdm
import json

class FloodRisk:
    def __init__(self, iso2, iso3, gid = None):
        self.iso2 = iso2
        self.iso3 = iso3
        self.gid = gid

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
        self.gid = level
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
        chunksize = 100000
        output_path = f"{path}/processed_cell_towers_{self.iso3.upper()}_{code}.shp"
        if os.path.exists(output_path):
            print(f"{output_path} already exists")

        features = []

        for chunk in tqdm(pd.read_csv(f"/home/cisc/projects/open-rigbi/scripts/FloodRisk/data/cell_towers_2022-12-24.csv", chunksize=chunksize)):
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

        if features:
            if int(level) == 0:
                all_features = gpd.GeoDataFrame(pd.concat(features, ignore_index=True))
                all_features.to_file(f"{path}/processed_cell_towers_{self.iso3.upper()}_{code}.shp")
                print(f"Saved {code} data to {output_path}")
                gid = gpd.read_file(f"/home/cisc/projects/open-rigbi/scripts/FloodRisk/data/processed/{self.iso3}/regions/regions_{level}_{self.iso3}.shp")
                all_features = gpd.sjoin(all_features, gid, how="inner", predicate="intersects")
                print(all_features.columns)
                return all_features
            else:
                joined_features = []
                for idx, f in enumerate(features):
                    f.to_csv(f"{path}/processed_cell_towers_{self.iso3.upper()}_{code}_{idx}.csv")
                    print(f"Saved {code}, {idx} data to {output_path}")
                    gid = gpd.read_file(f"/home/cisc/projects/open-rigbi/scripts/FloodRisk/data/processed/{self.iso3}/regions/regions_{level}_{self.iso3}.shp")
                    joined = gpd.sjoin(f, gid, how="inner", predicate="intersects")
                    joined_features.append(joined)
                if joined_features:
                    combined = pd.concat(joined_features, ignore_index=True)
                    combined = gpd.GeoDataFrame(combined)
                    return combined
                else:
                    print("No features to concatenate.")
                    return gpd.GeoDataFrame()

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

    def process_flooding_layers(self, country):
        """
        Loop to process all flood layers.

        """
        scenarios = get_scenarios()
        iso3 = country['iso3']
        name = country['country']

        hazard_dir = "/home/cisc/projects/open-rigbi/scripts/FloodRisk/data/raw/flood_hazard"

        failures = []

        for scenario in scenarios:

            #if 'river' in scenario:
            #    continue

            # if not os.path.basename(scenario) == 'inunriver_rcp4p5_0000HadGEM2-ES_2050_rp00500.tif':
            #    continue

            filename = os.path.basename(scenario).replace('.tif','')
            path_in = os.path.join(hazard_dir, filename + '.tif')

            folder = os.path.join(DATA_PROCESSED, self.iso3, 'hazards', 'flooding')
            if not os.path.exists(folder):
                os.makedirs(folder)
            path_out = os.path.join(folder, filename + '.tif')

            # if os.path.exists(path_out):
            #     continue

            print('--{}: {}'.format(name, filename))

            if not os.path.exists(folder):
                os.makedirs(folder)

            try:
                self.process_flood_layer(country, path_in, path_out)
            except:
                print('{} failed: {}'.format(country['iso3'], scenario))
                failures.append({
                    'iso3': country['iso3'],
                    'filename': filename
                })
                continue

        return

    def process_regional_flood_layer(self, country, path_in, path_out):
        """
        Clip the hazard layer to the chosen country boundary
        and place in desired country folder.

        Parameters
        ----------
        country : dict
            Contains all desired country information.
        path_in : string
            The path for the chosen global hazard file to be processed.
        path_out : string
            The path to write the clipped hazard file.

        """
        iso3 = self.iso3
        regional_level = self.gid

        hazard = rasterio.open(path_in, 'r+', BIGTIFF='YES')

        hazard.nodata = 255
        hazard.crs.from_epsg(4326)

        iso3 = country['iso3']
        path_country = os.path.join(DATA_PROCESSED, iso3,
            'national_outline.shp')

        if os.path.exists(path_country):
            country = gpd.read_file(path_country)
        else:
            print('Must generate national_outline.shp first' )

        # if os.path.exists(path_out):
        #     return

        geo = gpd.GeoDataFrame()

        geo = gpd.GeoDataFrame({'geometry': country['geometry']})

        coords = [json.loads(geo.to_json())['features'][0]['geometry']]

        out_img, out_transform = mask(hazard, coords, crop=True)

        depths = []

        for idx, row in enumerate(out_img[0]):
            for idx2, i in enumerate(row):
                if i > 0.001 and i < 150:
                    depths.append(i)
                else:
                    continue
        if sum(depths) < 0.01:
            return

        out_meta = hazard.meta.copy()

        out_meta.update({"driver": "GTiff",
                        "height": out_img.shape[1],
                        "width": out_img.shape[2],
                        "transform": out_transform,
                        "crs": 'epsg:4326',
                        "compress": 'lzw'})

        with rasterio.open(path_out, "w", **out_meta) as dest:
                dest.write(out_img)

        return

    def process_regional_flooding_layers(self, country):
        """
        Process each flooding layer at the regional level.

        """
        scenarios = get_scenarios()
        iso3 = country['iso3']
        name = country['country']
        region = self.gid

        filename = 'coastal_lookup.csv'
        folder = os.path.join(DATA_PROCESSED, iso3, 'coastal')
        path_coastal = os.path.join(folder, filename)
        if not os.path.exists(path_coastal):
            coastal_lut = []
        else:
            coastal_lut = pd.read_csv(path_coastal)
            coastal_lut = list(coastal_lut['gid_id'])

        hazard_dir = os.path.join(DATA_PROCESSED, iso3, 'hazards', 'flooding')

        for scenario in scenarios:

            #if 'river' in scenario:
            #    continue

            #if not os.path.basename(scenario) == 'inuncoast_rcp8p5_wtsub_2080_rp1000_0.tif':
            #    continue
            
            if 'inuncoast' in scenario and region not in coastal_lut:
                print('Not a coastal region: {}'.format(region))
                continue

            filename = os.path.basename(scenario).replace('.tif','')
            path_in = os.path.join(hazard_dir, filename + '.tif')

            if not os.path.exists(path_in):
                continue

            folder = os.path.join(DATA_PROCESSED, iso3, 'hazards', 'flooding', 'regional')
            # folder = os.path.join(DATA_PROCESSED, iso3, 'hazards', 'flooding', 'regional2', scenario)
            if not os.path.exists(folder):
                os.makedirs(folder)
            path_out = os.path.join(folder, region + '_' + filename + '.tif')

            # if os.path.exists(path_out):
            #     continue

            print('--{}: {}'.format(region, filename))

            try:
                self.process_regional_flood_layer(country, region, path_in, path_out)
            except:
                print('{} failed: {}'.format(region, scenario))
                continue
        return