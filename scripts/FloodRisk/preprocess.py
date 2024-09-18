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

    def create_sites_layer(country, regional_level, region, polygon):
        """
        Process cell estimates into an estimated site layer.

        """
        gid_level = "gid_{}".format(regional_level)
        filename = "{}_unique.csv".format(region)
        folder = os.path.join(DATA_PROCESSED, country['iso3'], 'sites', gid_level)
        path_out = os.path.join(folder, filename)
        
        # if os.path.exists(path_out):
        #     return

        filename = "{}.csv".format(region)
        folder = os.path.join(DATA_PROCESSED, country['iso3'], 'sites', gid_level)
        path = os.path.join(folder, filename)

        if not os.path.exists(path):
            return

        data = pd.read_csv(path)#[:500]

        data = convert_to_gpd_df(data)
        
        if polygon.type == 'Polygon':
            polygon_df = gpd.GeoDataFrame({'geometry': polygon}, index=[0], crs='epsg:4326')
        elif polygon.type == 'MultiPolygon':
            polygon_df = gpd.GeoDataFrame({'geometry': polygon.geoms}, crs='epsg:4326')

        data = gpd.overlay(data, polygon_df, how='intersection')
        
        data['bs_id_float'] = data['cell'] / 256
        data['bs_id_int'] = np.round(data['bs_id_float'],0)
        data['sector_id'] = data['bs_id_float'] - data['bs_id_int']
        data['sector_id'] = np.round(data['sector_id'].abs() * 256)
        # data.to_csv(path_out, index=False)
        
        unique_operators = data['net'].unique()
        unique_cell_ids = data['bs_id_int'].unique()
        unique_radios = data['radio'].unique()

        data = data.to_dict('records')
        
        sites = []

        for unique_operator in unique_operators:
            for unique_cell_id in unique_cell_ids:
                for unique_radio in unique_radios:

                    latitudes = []
                    longitudes = []

                    for row in data:
                        
                        if not unique_operator == row['net']:
                            continue 

                        if not unique_cell_id == row['bs_id_int']:
                            continue

                        if not unique_radio == row['radio']:
                            continue

                        lon, lat = row['cellid4326'].split("_")
                        latitudes.append(float(lat))
                        longitudes.append(float(lon))

                    if len(latitudes) == 0:
                        continue
                    latitude = sum(latitudes) / len(latitudes)

                    if len(longitudes) == 0:
                        continue
                    longitude = sum(longitudes) / len(longitudes)

                    sites.append({
                        "radio": unique_radio,
                        "net": unique_operator,
                        "cell_id": unique_cell_id,
                        "latitude": latitude,
                        "longitude": longitude,
                        "cellid4326": "{}_{}".format(latitude, longitude)
                    })

        if len(sites) == 0:
            return
            
        filename = 'regions_{}_{}.shp'.format(regional_level, iso3)
        folder = os.path.join(DATA_PROCESSED, iso3, 'regions')
        path_regions = os.path.join(folder, filename)
        regions = gpd.read_file(path_regions, crs='epsg:4326')#[:1]
        gid_level = "GID_{}".format(regional_level)
        region_df = regions[regions[gid_level] == region]['geometry'].values[0]

        output = []

        for site in sites:

            geom = Point(site['longitude'], site['latitude'])

            if not region_df.contains(geom):
                continue
            
            output.append({
                "radio": site['radio'],
                "net": site['net'],
                "cell_id": site['cell_id'],
                "latitude": site['latitude'],
                "longitude": site['longitude'],
                "cellid4326": site['cellid4326'],
            })

        output = pd.DataFrame(output)

        #filename = "{}_unique.csv".format(region)
        #folder = os.path.join(DATA_PROCESSED, country['iso3'], 'sites', gid_level)
        #path_out = os.path.join(folder, filename)
        output.to_csv(path_out, index=False)

        return

    def create_national_sites_csv(self, country):
        """
        Create a national sites csv layer for a selected country.

        """
        iso3 = country['iso3']#.values[0]

        filename = "mobile_codes.csv"
        path = os.path.join(DATA_RAW, filename)
        mobile_codes = pd.read_csv(path)
        mobile_codes = mobile_codes[['iso3', 'mcc', 'mnc']].drop_duplicates()
        all_mobile_codes = mobile_codes[mobile_codes['iso3'] == iso3]
        all_mobile_codes = all_mobile_codes.to_dict('records')

        output = []

        filename = '{}.csv'.format(iso3)
        folder = os.path.join(DATA_PROCESSED, iso3, 'sites')
        path_csv = os.path.join(folder, filename)

        ### Produce national sites data layers
        if os.path.exists(path_csv):
            return

        print('-site.csv data does not exist')
        print('-Subsetting site data for {}'.format(iso3))

        if not os.path.exists(folder):
            os.makedirs(folder)

        filename = "cell_towers_2022-12-24.csv"
        path = os.path.join(DATA_RAW, filename)

        for row in all_mobile_codes:

            # if not row['mnc'] in [10,2,11,33,34,20,94,30,31,32,27,15,91,89]:
            #     continue

            mcc = row['mcc']
            seen = set()
            chunksize = 10 ** 6
            for idx, chunk in enumerate(pd.read_csv(path, chunksize=chunksize)):

                country_data = chunk.loc[chunk['mcc'] == mcc]#[:1]

                country_data = country_data.to_dict('records')

                for site in country_data:

                    # if not -4 > site['lon'] > -6:
                    #     continue

                    # if not 49.8 < site['lat'] < 52:
                    #     continue

                    if site['cell'] in seen:
                        continue

                    seen.add(site['cell'])

                    output.append({
                        'radio': site['radio'],
                        'mcc': site['mcc'],
                        'net': site['net'],
                        'area': site['area'],
                        'cell': site['cell'],
                        'unit': site['unit'],
                        'lon': site['lon'],
                        'lat': site['lat'],
                        # 'range': site['range'],
                        # 'samples': site['samples'],
                        # 'changeable': site['changeable'],
                        # 'created': site['created'],
                        # 'updated': site['updated'],
                        # 'averageSignal': site['averageSignal']
                    })
                # if len(output) > 0:
                #     break

        if len(output) == 0:
            return

        output = pd.DataFrame(output)
        output.to_csv(path_csv, index=False)

        return


    def create_national_sites_shp(self, iso3):
        """
        Create a national sites csv layer for a selected country.

        """
        filename = '{}.csv'.format(iso3)
        folder = os.path.join(DATA_PROCESSED, iso3, 'sites')
        path_csv = os.path.join(folder, filename)

        filename = '{}.shp'.format(iso3)
        path_shp = os.path.join(folder, filename)

        if not os.path.exists(path_shp):

            # print('-Writing site shapefile data for {}'.format(iso3))

            country_data = pd.read_csv(path_csv)#[:10]
            country_data = country_data.to_dict('records')

            output = []

            for row in country_data:
                output.append({
                    'type': 'Feature',
                    'geometry': {
                        'type': 'Point',
                        'coordinates': [row['lon'],row['lat']]
                    },
                    'properties': {
                        'radio': row['radio'],
                        'mcc': row['mcc'],
                        'net': row['net'],
                        'area': row['area'],
                        'cell': row['cell'],
                    }
                })

            output = gpd.GeoDataFrame.from_features(output, crs='epsg:4326')

            output.to_file(path_shp)

    def process_flooding_layers(self, country):
        """
        Loop to process all flood layers.

        """
        scenarios = get_scenarios()
        iso3 = country['iso3']
        name = country['country']

        hazard_dir = os.path.join(DATA_RAW, 'flood_hazard')

        failures = []

        for scenario in scenarios:

            #if 'river' in scenario:
            #    continue

            # if not os.path.basename(scenario) == 'inunriver_rcp4p5_0000HadGEM2-ES_2050_rp00500.tif':
            #    continue

            filename = os.path.basename(scenario).replace('.tif','')
            path_in = os.path.join(hazard_dir, filename + '.tif')

            folder = os.path.join(DATA_PROCESSED, iso3, 'hazards', 'flooding')
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

    def create_national_sites_shp(self, iso3):
        """
        Create a national sites csv layer for a selected country.

        """
        filename = '{}.csv'.format(iso3)
        folder = os.path.join(DATA_PROCESSED, iso3, 'sites')
        path_csv = os.path.join(folder, filename)

        filename = '{}.shp'.format(iso3)
        path_shp = os.path.join(folder, filename)

        if not os.path.exists(path_shp):

            # print('-Writing site shapefile data for {}'.format(iso3))

            country_data = pd.read_csv(path_csv)#[:10]
            country_data = country_data.to_dict('records')

            output = []

            for row in country_data:
                output.append({
                    'type': 'Feature',
                    'geometry': {
                        'type': 'Point',
                        'coordinates': [row['lon'],row['lat']]
                    },
                    'properties': {
                        'radio': row['radio'],
                        'mcc': row['mcc'],
                        'net': row['net'],
                        'area': row['area'],
                        'cell': row['cell'],
                    }
                })

            output = gpd.GeoDataFrame.from_features(output, crs='epsg:4326')

            output.to_file(path_shp)


    def process_flood_layer(self, country, path_in, path_out):
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
        iso3 = country['iso3']
        regional_level = country['gid_region']

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

    def process_regional_flooding_layers(self, country, region):
        """
        Process each flooding layer at the regional level.

        """
        scenarios = get_scenarios()
        iso3 = country['iso3']
        name = country['country']

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


    def process_regional_flood_layer(self, country, region, path_in, path_out):
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
        iso3 = country['iso3']
        regional_level = int(country['gid_region'])
        gid_level = 'GID_{}'.format(regional_level)

        hazard = rasterio.open(path_in, 'r+', BIGTIFF='YES')
        hazard.nodata = 255
        hazard.crs.from_epsg(4326)

        iso3 = country['iso3']
        filename = 'regions_{}_{}.shp'.format(regional_level, iso3)
        path_country = os.path.join(DATA_PROCESSED, iso3, 'regions', filename)

        if os.path.exists(path_country):
            regions = gpd.read_file(path_country)
            region = regions[regions[gid_level] == region]
        else:
            print('Must generate national_outline.shp first' )
            return

        geo = gpd.GeoDataFrame()
        geo = gpd.GeoDataFrame({'geometry': region['geometry']})
        coords = [json.loads(geo.to_json())['features'][0]['geometry']]

        out_img, out_transform = mask(hazard, coords, crop=True)

        depths = []
        for idx, row in enumerate(out_img[0]):
            for idx2, i in enumerate(row):
                if i > 0.001 and i < 150:
                    # coords = raster.transform * (idx2, idx)
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
                        "crs": 'epsg:4326'})

        with rasterio.open(path_out, "w", **out_meta) as dest:
                dest.write(out_img)

        return
