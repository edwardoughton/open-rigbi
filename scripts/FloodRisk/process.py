#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# main.py file for OpenRigbi, designed to viusalize risk to telecom
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

import geopandas as gpd
import numpy as np
import pyproj
# import rasterio
# from rasterstats import zonal_stats
from shapely.geometry import Polygon, Point
import snail.intersection
import snail.io

import os
import re
from pathlib import Path
from typing import Optional

class GID:
    """
    Class representing a geographical area of interest and associated telecom infrastructure.

    Attributes:
        iso2 (str): ISO 3166-1 alpha-2 country code.
        iso3 (str): ISO 3166-1 alpha-3 country code.

    """

    def __init__(self, iso2: str, iso3: str, flood_path: str = None, buffer_distance: float = 10) -> None:
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

    def dms_to_decimal(self, dms, *args):
        # Regular expression pattern to match degrees, minutes, and seconds
        pattern = r"(\d+)º\s*(\d+)'\s*([\d.]+)\""

        # Function to convert a single DMS string to decimal degrees
        def convert_dms(dms_str):
            match = pattern.search(dms_str.replace(',', ''))  # Remove commas before searching
            match = re.match(pattern, dms_str)
            if match:
                degrees = float(match.group(1))
                minutes = float(match.group(2))
                seconds = float(match.group(3))
                return degrees + (minutes / 60 ) + (seconds / 3600)
            else:
                raise ValueError(f"Invalid DMS coordinate format: {dms_str}")

        # Update the specified columns
        for col in args:
            dms[col] = dms[col].apply(convert_dms)

        return dms

    def convert_csv_dms_to_decimal(self, df, *dms_columns):
        """
        Convert columns containing DMS coordinates to decimal degrees.

        Args:
            df (pd.DataFrame): DataFrame containing DMS coordinates.
            dms_columns (List[str]): List of column names containing DMS coordinates.

        Returns:
            pd.DataFrame: DataFrame with DMS coordinates converted to decimal degrees.
        """
        for col in dms_columns:
            if col in df.columns:
                df[col].apply(self.dms_to_decimal)
            else:
                print(f"Column {col} not found in DataFrame")
        return df

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

    """def get_pop_data(self, country: Dict) -> pd.DataFrame:
        Retrieve regional population and luminosity data for a given country.

        Args:
            country (Dict): Dictionary containing country information including iso3 code and regional level.

        Returns:
            pd.DataFrame: A DataFrame containing regional data including population and area information.

        Note:
            The code within this method is adapted from the PyTal library, 
            which was written by Dr. Edward John Oughton and Tom Russel.

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

                Get a lat, lon, id for each cell site
                Utilize this line to get population summation
                Replace region['geometry'] with my buffered zones

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

        # Possibly export as a CSV file or add as a tag to one of the sites
        results_df: pd.DataFrame = pd.DataFrame(results)
        return results_df
        """
    
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

        if telecom_features is not None:
            print(f"Number of telecom points before buffering: {len(telecom_features)}")  # Debug print

            buffer_distance_km = self.buffer_distance
            telecom_buffers = GID.create_buffers(telecom_features, buffer_distance_km)
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
                flood_intersections = flood_intersections[['bs_id_int', 'sector_id']]
                print(flood_intersections.tail(5))
                print(flood_intersections.columns)

                print(len(flood_intersections))
                overlaid_csv_path = f"telecom_with_flood_{self.iso2}.csv"
                flood_intersections.to_csv(EXPORTS_FOLDER / f"{self.iso3}" / f"{overlaid_csv_path}_{feature_name}_{scenario_name}")

                # Print all of this to the screen
                print(f"Telecom features with flood intersections saved as CSV: {overlaid_csv_path}")
            else:
                print("No buffers created around telecom points.")
        else:
            print("No telecom features found for the provided country code.")