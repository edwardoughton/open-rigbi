#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# main.py file for OpenRigbi, designed to visalize risk to telecom
# infrastructure due to natural disasters
#
# SPDX-FileCopyrightText: 2024 Aryaman Rajaputra <arajaput@gmu.edu>
# SPDX-License-Identifier: MIT
#
# Note: The programs and configurations used by this script may not be under the same license.
# Please check the LICENSING file in the root directory of this repository for more information.
#
# This script was created by Aryaman Rajaputra

import geopandas as gpd
import numpy as np
import pandas as pd
import pyproj
import rasterio
from rasterstats import zonal_stats
from shapely.geometry import Polygon, Point
import snail.intersection
import snail.io
import tqdm

import math
import re
import os
from pathlib import Path
from typing import Dict, List, Optional

BASE_PATH: str = './data'
DATA_FOLDER: Path = Path('./data')
DATA_RAW: str = os.path.join(BASE_PATH, 'raw')
DATA_INTERMEDIATE: str = os.path.join(BASE_PATH, 'intermediate')
DATA_PROCESSED: str = os.path.join(BASE_PATH, 'processed')
EXPORTS_FOLDER: Path = DATA_FOLDER / 'exports'
EXPORTS_FOLDER.mkdir(parents=True, exist_ok=True)

class GID:
    """
    Class representing a geographical area of interest and associated telecom infrastructure.

    Attributes:
        iso2 (str): ISO 3166-1 alpha-2 country code.
        iso3 (str): ISO 3166-1 alpha-3 country code.

    """

    def __init__(self, iso2: str, iso3: str, flood_path: str, buffer_distance: float = 10) -> None:
        """
        Initialize GIDTwo object with given region and optional telecom infrastructure.

        Args:
            iso2 (str): ISO 3166-1 alpha-2 country code.
            iso3 (str): ISO 3166-1 alpha-3 country code.
            buffer_distance (float, optional): The distance in units to buffer the region. Defaults to 10.
        """
        self.iso2: str = iso2
        self.iso3: str = iso3
        self.flood_path = flood_path
        self.buffer_distance = buffer_distance

    def save_as_shapefile(self, gdf: gpd.GeoDataFrame, filename: str, crs: str = 'EPSG:4326') -> None:
        """
        Save a GeoDataFrame as a shapefile.

        Args:
            gdf (gpd.GeoDataFrame): The GeoDataFrame to save.
            filename (str): The filename for the shapefile.
            crs (str, optional): The coordinate reference system to use. Defaults to 'EPSG:4326'.
        """
        if gdf is not None and not gdf.empty:
            gdf = gdf.to_crs(crs)

            country_folder = EXPORTS_FOLDER / self.iso3
            country_folder.mkdir(parents=True, exist_ok=True)

            filepath = country_folder / filename
            gdf.to_file(filepath)
            print("Telecom features data saved as:", filepath)
        else:
            print("No telecom features found for the provided country code.")

    def preprocess(self):
        path = f"../data/processed/{self.iso3.upper()}/regions"
        features = []
        total_rows = sum(1 for _ in open("../data/raw/cell_towers_2022-12-24.csv")) - 1  # Subtract 1 for the header row
        chunksize = 1000

        total_chunks = math.ceil(total_rows / chunksize)
        chunk_count = 0

        for chunk in tqdm(pd.read_csv("../data/raw/cell_towers_2022-12-24.csv", chunksize=chunksize), total=total_chunks, desc="Processing chunks"):

            # Filter rows by MCC codes
            chunk = chunk[chunk["mcc"] == 204]

            if not chunk.empty:
                chunk['geometry'] = [Point(row.lon, row.lat) for row in chunk.itertuples()]
                gdf_chunk = gpd.GeoDataFrame(chunk, geometry='geometry')
                features.append(gdf_chunk)
                chunk_count += 1
                print(f"Created chunk {chunk_count}/{total_chunks}")

        all_features = pd.concat(features, ignore_index=True)

        output_path = f"{path}/processed_cell_towers_{self.iso3.upper()}.shp"
        all_features.to_file(output_path)

        return all_features
    
    @staticmethod
    def convert_to_stations(data):
        data['bs_id_float'] = data['cell'] / 256
        data['bs_id_int'] = np.round(data['bs_id_float'], 0)
        data['sector_id'] = data['bs_id_float'] - data['bs_id_int']
        data['sector_id'] = np.round(data['sector_id'].abs() * 256)

    def dms_to_decimal(dms):
        """
        https://stackoverflow.com/questions/33997361/how-to-convert-degree-minute-second-to-degree-decimal
        """
        deg, minutes, seconds, direction =  re.split('[°\'"]', dms)
        decimal = (float(deg) + float(minutes)/60 + float(seconds)/(60*60)) * (-1 if direction in ['W', 'S'] else 1)
        return decimal

    def convert_csv_dms_to_decimal(self, df, dms_columns):
        for col in dms_columns:
            df[col] = df[col].apply(self.dms_to_decimal)
        return df

    def compare_data(self, ocid, radio):
        ocid = gpd.read_file(ocid)
        radio = pd.read_csv(radio, skiprows=[0, 1, 2, 3, 4])

        # Finding latitude and longitude columns in the CSV DataFrame
        for col in radio.columns:
            if 'coördinaten noorderbreedte' in col.lower():
                radio_lat_col = col
            elif 'coördinaten oosterlengte' in col.lower():
                radio_lon_col = col

        if not (radio_lat_col and radio_lon_col):
            raise ValueError("Latitude or Longitude columns not found in the CSV")

        # Converting DMS coordinates in CSV to decimal
        radio = self.convert_csv_dms_to_decimal(radio, [radio_lat_col, radio_lon_col])

        ocid_points = ocid['geometry']
        radio_points = [Point(lon, lat) for lon, lat in zip(radio[radio_lon_col], radio[radio_lat_col])]

        missing_entries = []
        for idx, point in tqdm(enumerate(radio_points), total=len(radio_points), desc="Comparing coordinates"):
            if point not in ocid_points:
                missing_entries.append(radio.iloc[idx])

        missing_df = pd.DataFrame(missing_entries)
        missing_df['Source'] = 'OCID'
        return missing_df

    @staticmethod
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
        
    @staticmethod
    def area_of_polygon(geom: Polygon) -> float:
        """
        Calculate the area of a given polygon, assuming WSG84 as the CRS.

        Args:
            geom (Polygon): The polygon geometry.

        Returns:
            float: The area of the polygon in square meters.
        """
        geod: pyproj.Geod = pyproj.Geod(ellps="WGS84")

        poly_area, _ = geod.geometry_area_perimeter(geom)

        return abs(poly_area)

    def get_pop_data(self, country: Dict) -> pd.DataFrame:
        """
        Retrieve regional population and luminosity data for a given country.

        Args:
            country (Dict): Dictionary containing country information including iso3 code and regional level.

        Returns:
            pd.DataFrame: A DataFrame containing regional data including population and area information.

        Note:
            The code within this method is adapted from the PyTal library, 
            which was written by Dr. Edward John Oughton and Tom Russel.
        """

        iso3: str = country['iso3']
        level: str = country['regional_level']
        gid_level: str = 'GID_{}'.format(level)

        print('----')
        print('Working on population data for {}'.format(iso3))

        path_settlements: str = os.path.join(DATA_INTERMEDIATE, iso3, 'settlements.tif')

        filename: str = 'regions_{}_{}.shp'.format(level, iso3)
        folder: str = os.path.join(DATA_INTERMEDIATE, iso3, 'regions')
        path: str = os.path.join(folder, filename)

        regions: gpd.GeoDataFrame = gpd.read_file(path)

        results: List[Dict[str, float]] = []

        for _, region in regions.iterrows():

            with rasterio.open(path_settlements) as src:

                affine = src.transform
                array = src.read(1)
                array[array <= 0] = 0

                """
                Get a lat, lon, id for each cell site
                Utilize this line to get population summation
                Replace region['geometry'] with my buffered zones
                """
                population_summation = [d['sum'] for d in zonal_stats(
                    region['geometry'], array, stats=['sum'], affine=affine)][0]

            area_km2: float = round(self.area_of_polygon(region['geometry']) / 1e6)

            if area_km2 > 0:
                population_km2: float = (
                    population_summation / area_km2 if population_summation else 0)
            else:
                population_km2: float = 0

            results.append({
                'GID_0': region['GID_0'],
                'GID_id': region[gid_level],
                'GID_level': gid_level,
                'population': (population_summation if population_summation else 0),
                'area_km2': area_km2,
                'population_km2': population_km2,
            })

        """Possibly export as a CSV file or add as a tag to one of the sites"""
        results_df: pd.DataFrame = pd.DataFrame(results)
        return results_df

    
    def process(self) -> None:
        """
        Download, prepare, and intersect flood data with a given regional layer.

        Note:
            This code is mostly adapted from code provided by Mr. Tom Russel from Oxford University.
        """
        telecom_features = self.preprocess()
        if telecom_features is not None:
            print(f"Number of telecom points before buffering: {len(telecom_features)}")  # Debug print

            buffer_distance_km = self.buffer_distance
            telecom_buffers = GID.create_buffers(telecom_features, buffer_distance_km)
            if telecom_buffers is not None:
                print(f"Number of buffered telecom points: {len(telecom_buffers)}")  # Debug print

                self.save_as_shapefile(telecom_buffers, f"telecom_buffers_{self.iso2}.shp")
                print(f"Number of telecom points after saving shapefile: {len(telecom_features)}")  # Debug print 

                flood_path = Path(
                    DATA_FOLDER,
                    "flood_layer",
                    f"{self.iso3.lower()}",
                    "wri_aqueduct_version_2",
                    f"{self.flood_path.lower()}"
                )

                grid, _ = snail.io.read_raster_metadata(flood_path)
                prepared = snail.intersection.prepare_points(telecom_features)
                flood_intersections = snail.intersection.split_points(prepared, grid)

                flood_intersections = snail.intersection.apply_indices(flood_intersections, grid)
                flood_data = snail.io.read_raster_band_data(flood_path)
                flood_intersections["inun"] = snail.intersection.get_raster_values_for_splits(
                    flood_intersections, flood_data
                )

                # Debug printing
                print(flood_intersections.tail(5))
                print(flood_intersections.columns)

                print(len(flood_intersections))
                overlaid_csv_path = f"telecom_with_flood_{self.iso2}.csv"
                flood_intersections.to_csv(EXPORTS_FOLDER / overlaid_csv_path, columns=['geometry', 'inun'])

                # Print all of this to the screen
                print(f"Telecom features with flood intersections saved as CSV: {overlaid_csv_path}")
            else:
                print("No buffers created around telecom points.")
        else:
            print("No telecom features found for the provided country code.")

if __name__ == "__main__":
    country_code = input("Enter the ISO 3166-1 alpha-2 country code: ").upper().strip()
    country_code_3 = input("Enter the ISO 3166-1 alpha-3 country code: ").upper().strip()
    flood_scenario = input("Enter the *name* of the scenario you wish to run (not the full path): ")
    print("Country code entered:", country_code)
    g = GID(country_code, country_code_3, flood_scenario)
    g.process()

"""
TODO: 2024-05-24
Download all OSM cell ID data for the world.

TODO: Get flood depth/wind speed for each station.

TODO: Break file into components for preprocessing and post processing.
TODO: Implement checks for if a country's data already exists, then don't re-run the script.
TODO: Create centroids for the bands and then divide by 256.
"""
