#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# main.py file for FloodRisk, designed to visalize risk to telecom
# infrastructure due to flooding
#
# SPDX-FileCopyrightText: 2024 Aryaman Rajaputra <arajaput@gmu.edu>
# SPDX-License-Identifier: MIT
#
# Note: The programs and configurations used by this script may not be under the same license.
# Please check the LICENSING file in the root directory of this repository for more information.
#
# This script was created by Aryaman Rajaputra

import requests
import geopandas as gpd
from shapely.geometry import Point, LineString
from pyproj import Geod
import snkit
import snail.intersection
import snail.io

from pathlib import Path
from typing import Union, Optional

DATA_FOLDER = Path('./data')

def get_telecom_features(country_code: str) -> Optional[gpd.GeoDataFrame]:
    """
    Fetches telecom features data for a given country code using Overpass API.

    Args:
        country_code (str): ISO 3166-1 alpha-2 country code.

    Returns:
        gpd.GeoDataFrame or None: GeoDataFrame containing telecom features if successful, else None.
    """
    print("Fetching telecom features data for country:", country_code)
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json];
    area["ISO3166-1"="{country_code}"]->.searchArea;
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

        gdf.crs = 'EPSG:4326'
        print("Telecom features data fetched successfully.")
        return gdf
    else:
        print("Error fetching telecom features data. Status code:", response.status_code)
        return None

def save_as_shapefile(gdf: gpd.GeoDataFrame, filename: str, crs: str = 'EPSG:4326') -> None:
    """
    Saves GeoDataFrame as a shapefile.

    Args:
        gdf (gpd.GeoDataFrame): GeoDataFrame to be saved.
        filename (str): Name of the output shapefile.
        crs (str, optional): Coordinate Reference System. Defaults to 'EPSG:4326'.
    """
    if gdf is not None and not gdf.empty:
        gdf.to_file(filename, crs=crs)
        print("Telecom features data saved as:", filename)
    else:
        print("No telecom features found for the provided country code.")

def create_line_segments_with_tags(points: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Creates line segments with tags from a GeoDataFrame of points.

    Args:
        points (gpd.GeoDataFrame): GeoDataFrame containing telecom points.

    Returns:
        gpd.GeoDataFrame: GeoDataFrame containing line segments with tags.
    """
    print("Creating line segments with tags...")
    lines = []
    for i in range(len(points)):
        for j in range(i+1, len(points)):
            point1 = points.iloc[i]['geometry']
            point2 = points.iloc[j]['geometry']
            line = LineString([point1, point2])
            tags = {'type': 'telecom_line'}
            lines.append({'geometry': line, 'tags': tags})

    gdf = gpd.GeoDataFrame(lines, columns=['geometry', 'tags'])
    print("Line segments with tags created successfully.")
    return gdf

def create_buffers(telecom_points: gpd.GeoDataFrame, buffer_distance_km: float) -> Union[gpd.GeoDataFrame, None]:
    """
    Creates buffers around telecom points.

    Args:
        telecom_points (gpd.GeoDataFrame): GeoDataFrame containing telecom points.
        buffer_distance_km (float): Buffer distance in kilometers.

    Returns:
        Union[gpd.GeoDataFrame, None]: GeoDataFrame containing buffers if successful, else None.
    """
    print("Creating buffers around telecom points...")
    if not telecom_points.empty:
        geod = Geod(ellps="WGS84")
        
        buffer_distance_m = buffer_distance_km * 1000
        
        buffers = []
        for _, row in telecom_points.iterrows():
            lon, lat = row['geometry'].x, row['geometry'].y

            lon_buffer, lat_buffer, _ = geod.fwd(lon, lat, 0, buffer_distance_m)
            buffer_geom = Point(lon_buffer, lat_buffer).buffer(buffer_distance_m)
            buffers.append(buffer_geom)
        
        buffers_gdf = gpd.GeoDataFrame(geometry=buffers)
        buffers_gdf.crs = 'EPSG:4326'
        print("Buffers around telecom points created successfully.")
        return buffers_gdf
    else:
        print("No telecom points provided.")
        return None
    
def process(country_code: str) -> None:
    """
    Processes telecom data for a given country code.

    Args:
        country_code (str): ISO 3166-1 alpha-2 country code.

    Note:
        The code is this section is mainly based on code written by Mr. Russel
        at Oxford University as part of the nismod-snail library.

        The nismod-snail library is released under the MIT license.

        https://github.com/nismod/snail
    """
    telecom_features = get_telecom_features(country_code)
    save_as_shapefile(telecom_features, f"telecom_features_{country_code}.shp")

    telecom_lines = create_line_segments_with_tags(telecom_features)
    save_as_shapefile(telecom_lines, f"telecom_lines_{country_code}.shp")
    
    save_as_shapefile(telecom_features, f"telecom_points_{country_code}.shp")

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
        DATA_FOLDER / f"{country_code}_OSM_tele.gpkg",
        layer="edges",
        driver="GPKG",
    )
    print("Telecom edges saved.")

    print("Saving telecom nodes...")
    tele_nodes.to_file(
        DATA_FOLDER / f"{country_code}_OSM_tele.gpkg",
        layer="nodes",
        driver="GPKG",
    )
    print("Telecom nodes saved.")

    flood_path = Path(
        DATA_FOLDER,
        "flood_layer",
        "nld",
        "wri_aqueduct_version_2",
        "wri_aqueduct-version_2-inunriver_historical_000000000WATCH_1980_rp00100-nld.tif",
    )

    output_path = Path(
        DATA_FOLDER,
        "results",
        "inunriver_historical_000000000WATCH_1980_rp00100__tele_exposure.gpkg",
    )
   
    tele_re_read = gpd.read_file(DATA_FOLDER / f"{country_code}_OSM_tele.gpkg", layer="edges")
    grid, bands = snail.io.read_raster_metadata(flood_path)
    prepared = snail.intersection.prepare_linestrings(tele_re_read)
    flood_intersections = snail.intersection.split_linestrings(prepared, grid)
    flood_intersections = snail.intersection.apply_indices(flood_intersections, grid)
    flood_data = snail.io.read_raster_band_data(flood_path)
    flood_intersections[
        "inunriver__epoch_historical__rcp_baseline__rp_100"
    ] = snail.intersection.get_raster_values_for_splits(
        flood_intersections, flood_data
    )

    geod = Geod(ellps="WGS84")
    flood_intersections["flood_length_m"] = flood_intersections.geometry.apply(
        geod.geometry_length
    )

    print(flood_intersections.tail(2))

    exposed_1m = flood_intersections[
    flood_intersections.inunriver__epoch_historical__rcp_baseline__rp_100 >= 1
]
    exposed_length_km = exposed_1m.flood_length_m.sum() * 1e-3

    proportion = exposed_length_km / len(telecom_features['geometry'])

    flood_intersections_gdf = gpd.GeoDataFrame(flood_intersections, geometry='geometry', crs='EPSG:4326')

    telecom_with_flood = gpd.sjoin(telecom_features, flood_intersections_gdf, how="left", op="intersects")

    overlaid_shapefile_path = f"telecom_with_flood_{country_code}.shp"

    telecom_with_flood.to_file(overlaid_shapefile_path)

    print("Telecom features with flood intersections saved as shapefile:", overlaid_shapefile_path)
    print(f"{proportion:.1%} of telecom stations in this dataset are exposed to flood depths of >= 1m in a historical 1-in-100 year flood")

if __name__ == "__main__":
    country_code = input("Enter the ISO 3166-1 alpha-2 country code: ").upper().strip()
    print("Country code entered:", country_code)
    process(country_code)
    
