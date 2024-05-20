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
import requests
from shapely.geometry import LineString, Polygon, Point
import snail.intersection
import snail.io
import snkit

import os
from pathlib import Path
from typing import Dict, List, Optional

BASE_PATH: str = './data'
DATA_FOLDER: Path = Path('./data')
DATA_RAW: str = os.path.join(BASE_PATH, 'raw')
DATA_INTERMEDIATE: str = os.path.join(BASE_PATH, 'intermediate')
DATA_PROCESSED: str = os.path.join(BASE_PATH, 'processed')

class GIDTwo:
    """
    Class representing a geographical area of interest and associated telecom infrastructure.

    Attributes:
        iso2 (str): ISO 3166-1 alpha-2 country code.
        iso3 (str): ISO 3166-1 alpha-3 country code.
        telecom (Optional[gpd.GeoDataFrame]): A GeoDataFrame representing the existing telecom infrastructure.
        buffer_distance (float): The distance in units to buffer the region.
        centroids (List[Point]): A list to store centroid points of buffered geometries.
        buffer_index (int): Index used for buffering operations.
    """

    def __init__(self, iso2: str, iso3: str, buffer_distance: float = 10) -> None:
        """
        Initialize GIDTwo object with given region and optional telecom infrastructure.

        Args:
            iso2 (str): ISO 3166-1 alpha-2 country code.
            iso3 (str): ISO 3166-1 alpha-3 country code.
            buffer_distance (float, optional): The distance in units to buffer the region. Defaults to 10.
        """
        self.iso2: str = iso2
        self.iso3: str = iso3
        self.telecom: Optional[gpd.GeoDataFrame] = None
        self.buffer_distance: float = buffer_distance
        self.centroids: List[Point] = []
        self.buffer_index: int = 0

    def get_telecom_features(self) -> Optional[gpd.GeoDataFrame]:
        """
        Fetch telecom features data for the specified country from the Overpass API.

        Returns:
            Optional[gpd.GeoDataFrame]: GeoDataFrame containing telecom features or None if the request fails.
        """
        print(f"Fetching telecom features data for country: {self.iso2}")
        overpass_url = "http://overpass-api.de/api/interpreter"
        overpass_query = f"""
        [out:json];
        area["ISO3166-1"="{self.iso2}"]->.searchArea;
        (
        nwr["telecom"](area.searchArea);
        );
        out center;
        """

        response = requests.get(overpass_url, params={'data': overpass_query})

        if response.status_code == 200:
            data = response.json()

            features = []
            for element in data['elements']:
                if 'lat' in element and 'lon' in element:
                    lon = element['lon']
                    lat = element['lat']
                    point = Point(lon, lat)
                    tags = element.get('tags', {})
                    features.append({'geometry': point, 'tags': tags})

            gdf = gpd.GeoDataFrame(features, columns=['geometry', 'tags'])

            gdf.set_crs('EPSG:4326', inplace=True)
            print("Telecom features data fetched successfully.")
            return gdf
        else:
            print("Error fetching telecom features data. Status code:", response.status_code)
            return None

    @staticmethod
    def save_as_shapefile(gdf: gpd.GeoDataFrame, filename: str, crs: str = 'EPSG:4326') -> None:
        """
        Save a GeoDataFrame as a shapefile.

        Args:
            gdf (gpd.GeoDataFrame): The GeoDataFrame to save.
            filename (str): The filename for the shapefile.
            crs (str, optional): The coordinate reference system to use. Defaults to 'EPSG:4326'.
        """
        if gdf is not None and not gdf.empty:
            gdf = gdf.to_crs(crs)
            gdf.to_file(filename)
            print("Telecom features data saved as:", filename)
        else:
            print("No telecom features found for the provided country code.")

    @staticmethod
    def create_line_segments_with_tags(points: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Create line segments with tags from telecom points.

        Args:
            points (gpd.GeoDataFrame): GeoDataFrame containing telecom points.

        Returns:
            gpd.GeoDataFrame: GeoDataFrame containing line segments with tags.
        """
        print("Creating line segments with tags...")
        lines = []
        for i in range(len(points)):
            for j in range(i + 1, len(points)):
                point1 = points.iloc[i]['geometry']
                point2 = points.iloc[j]['geometry']
                line = LineString([point1, point2])
                tags = {'type': 'telecom_line'}
                lines.append({'geometry': line, 'tags': tags})

        gdf = gpd.GeoDataFrame(lines, columns=['geometry', 'tags'])
        gdf.set_crs('EPSG:4326', inplace=True)
        print("Line segments with tags created successfully.")
        return gdf

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
    
    def process(self) -> None:
        """
        Download, prepare, and intersect flood data with a given regional layer.

        Note:
            This code is mostly adapted from code provided by Mr. Tom Russel from Oxford University.
        """
        telecom_features = self.get_telecom_features()
        GIDTwo.save_as_shapefile(telecom_features, f"telecom_features_{self.iso2}.shp")

        telecom_lines = GIDTwo.create_line_segments_with_tags(telecom_features)
        GIDTwo.save_as_shapefile(telecom_lines, f"telecom_lines_{self.iso2}.shp")
        
        GIDTwo.save_as_shapefile(telecom_features, f"telecom_points_{self.iso2}.shp")

        telecom_network = snkit.Network(edges=telecom_lines)
        with_endpoints = snkit.network.add_endpoints(telecom_network)
        split_edges = snkit.network.split_edges_at_nodes(with_endpoints)
        with_ids = snkit.network.add_ids(split_edges, id_col="id", edge_prefix="telee", node_prefix="telen")
        connected = snkit.network.add_topology(with_ids)
        tele_edges = connected.edges
        tele_nodes = connected.nodes

        tele_edges.set_crs(4326, inplace=True)
        tele_nodes.set_crs(4326, inplace=True)

        print("Saving telecom edges...")
        tele_edges.to_file(
            DATA_FOLDER / f"{self.iso2}_OSM_tele.gpkg",
            layer="edges",
            driver="GPKG",
        )
        print("Telecom edges saved.")

        print("Saving telecom nodes...")
        tele_nodes.to_file(
            DATA_FOLDER / f"{self.iso2}_OSM_tele.gpkg",
            layer="nodes",
            driver="GPKG",
        )
        print("Telecom nodes saved.")

        buffer_distance_km = self.buffer_distance
        telecom_buffers = GIDTwo.create_buffers(telecom_features, buffer_distance_km)
        GIDTwo.save_as_shapefile(telecom_buffers, f"telecom_buffers_{self.iso2}.shp")

        print(f"Number of telecom points buffered: {len(telecom_features)}")

        flood_path = Path(
            DATA_FOLDER,
            "flood_layer",
            f"{self.iso3.lower()}",
            "wri_aqueduct_version_2",
            f"wri_aqueduct-version_2-inuncoast_rcp8p5_wtsub_2030_rp0100_0-nld.tif",
        )

        output_path = Path(
            DATA_FOLDER,
            "results",
            "inunriver_historical_000000000WATCH_1980_rp00100__tele_exposure.gpkg",
        )
    
        tele_re_read = gpd.read_file(DATA_FOLDER / f"{self.iso2}_OSM_tele.gpkg", layer="edges")
        grid, bands = snail.io.read_raster_metadata(flood_path)
        prepared = snail.intersection.prepare_linestrings(tele_re_read)
        flood_intersections = snail.intersection.split_linestrings(prepared, grid)
        flood_intersections = snail.intersection.apply_indices(flood_intersections, grid)
        flood_data = snail.io.read_raster_band_data(flood_path)
        flood_intersections[
            "wri_aqueduct-version_2-inuncoast_rcp8p5_wtsub_2030_rp0100_0-nld.tif"
        ] = snail.intersection.get_raster_values_for_splits(
            flood_intersections, flood_data
        )

        geod = pyproj.Geod(ellps="WGS84")
        flood_intersections["flood_length_m"] = flood_intersections.geometry.apply(
            geod.geometry_length
        )

        print(flood_intersections.tail(5))

        exposed_1m = flood_intersections[
        flood_intersections.inunriver__epoch_historical__rcp_baseline__rp_100 >= 1
        ]
        exposed_length_km = exposed_1m.flood_length_m.sum() * 1e-3

        proportion = exposed_length_km / len(telecom_features['geometry'])

        flood_intersections_gdf = gpd.GeoDataFrame(flood_intersections, geometry='geometry', crs='EPSG:4326')

        telecom_with_flood = gpd.sjoin(telecom_features, flood_intersections_gdf, how="left", op="intersects")

        overlaid_shapefile_path = f"telecom_with_flood_{self.iso2}.shp"

        telecom_with_flood.to_file(overlaid_shapefile_path)

        print(f"Telecom features with flood intersections saved as shapefile: {overlaid_shapefile_path}")
        print(f"{proportion:.1%} of telecom stations in this dataset are exposed to flood depths of >= 1m in a historical 1-in-100 year flood")

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
        raise NotImplementedError
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


if __name__ == "__main__":
    country_code = input("Enter the ISO 3166-1 alpha-2 country code: ").upper().strip()
    country_code_3 = input("Enter the ISO 3166-1 alpha-3 country code: ").upper().strip()
    print("Country code entered:", country_code)
    g = GIDTwo(country_code, country_code_3)
    g.process()
