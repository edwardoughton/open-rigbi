#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# telecom.py file for OpenRigbi, designed to visalize risk to telecom
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
import pandas as pd
import pyproj
import rasterio
from rasterstats import zonal_stats
from shapely.geometry import Polygon, Point
import snail.intersection
import snail.io

import os
from pathlib import Path
from typing import Dict, List, Optional

from osm import get_telecom_features

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

    def __init__(self, iso2: str, iso3: str, flood_path: str, flood_depth: str, buffer_distance: float = 10) -> None:
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
        self.flood_depth = flood_depth
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

        results_df: pd.DataFrame = pd.DataFrame(results)
        return results_df

    
    def process(self) -> None:
        """
        Download, prepare, and intersect flood data with a given regional layer.

        Note:
            This code is mostly adapted from code provided by Mr. Tom Russel from Oxford University.
        """
        telecom_features = get_telecom_features()
        if telecom_features is not None:
            self.save_as_shapefile(telecom_features, f"telecom_features_{self.iso2}.shp")
            print("Saving telecom points...")
            telecom_features.to_file(
                EXPORTS_FOLDER / f"{self.iso2.lower()}_OSM_tele.gpkg",
                layer="nodes",
                driver="GPKG",
            )

            buffer_distance_km = self.buffer_distance
            telecom_buffers = GID.create_buffers(telecom_features, buffer_distance_km)
            if telecom_buffers is not None:
                self.save_as_shapefile(telecom_buffers, f"telecom_buffers_{self.iso2}.shp")
                print(f"Number of telecom points buffered: {len(telecom_features)}")

                flood_path = Path(
                    DATA_FOLDER,
                    "flood_layer",
                    f"{self.iso3}",
                    "wri_aqueduct_version_2",
                    f"{self.flood_path.lower()}"
                )

                # Read in the geopkg
                # Read the raster data from the flood .tif file
                # Prepare the points for splitting (explode any multi-geometries into single geometries)
                # Split the points (this is a no-op on points)
                # Apply the i and j indices to the points
                # Read in the band data from the tif file from earlier
                # Look up the raster values from intersecting the flood data and store it to the "inun" column

                tele_re_read = gpd.read_file(EXPORTS_FOLDER / f"{self.iso2}_OSM_tele.gpkg", layer="nodes")
                grid, _ = snail.io.read_raster_metadata(flood_path)
                prepared = snail.intersection.prepare_points(tele_re_read)
                flood_intersections = snail.intersection.split_points(prepared, grid)
                flood_intersections = snail.intersection.apply_indices(flood_intersections, grid)
                flood_data = snail.io.read_raster_band_data(flood_path)
                flood_intersections[
                    "inun"
                ] = snail.intersection.get_raster_values_for_splits(
                    flood_intersections, flood_data
                )

                # Debug printing
                print(flood_intersections.tail(5))
                print(flood_intersections.columns)

                # Convert the intersections into their own data frame
                flood_intersections_gdf = gpd.GeoDataFrame(flood_intersections, geometry='geometry', crs='EPSG:4326')

                # Create a frame of the telecom features intersected with the flood intersections frame
                telecom_with_flood = gpd.sjoin(telecom_features, flood_intersections_gdf, how="left", op="intersects")

                # If the flooding depth at a given station or within the buffer of that station is >= to the value we defined:
                # save that to the affected stations list, else continue
                affected_stations = telecom_with_flood.dropna(subset=['index_right'])[telecom_with_flood['inun'] >= self.flood_depth]

                overlaid_shapefile_path = f"telecom_with_flood_{self.iso2}.shp"
                self.save_as_shapefile(affected_stations, overlaid_shapefile_path)

                # Get the number and proportion of affected stations
                intersected_count = len(affected_stations)
                total_count = len(telecom_features)
                proportion_intersected = intersected_count / total_count if total_count > 0 else 0

                # Print all of this to the screen
                print(f"Telecom features with flood intersections saved as shapefile: {overlaid_shapefile_path}")
                print(f"{proportion_intersected:.1%} of telecom stations in this dataset are exposed to flood depths of >= 1m in this flood simulation.")
            else:
                print("No buffers created around telecom points.")
        else:
            print("No telecom features found for the provided country code.")

if __name__ == "__main__":
    country_code = input("Enter the ISO 3166-1 alpha-2 country code: ").upper().strip()
    country_code_3 = input("Enter the ISO 3166-1 alpha-3 country code: ").upper().strip()
    flood_scenario = input("Enter the *name* of the scenario you wish to run (not the full path): ")
    flood_depth = float(input("Enter the flood depth you would like to test the scenario with (in metres): "))
    print("Country code entered:", country_code)
    g = GID(country_code, country_code_3, flood_scenario, flood_depth)
    g.process()
