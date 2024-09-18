#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# visualization.py file for FloodRisk, designed to visalize risk to telecom
# infrastructure due to flooding
#
# SPDX-FileCopyrightText: 2024 Aryaman Rajaputra <arajaput@gmu.edu>
# SPDX-License-Identifier: MIT
#
# Note: The programs and configurations used by this script may not be under the same license.
# Please check the LICENSING file in the root directory of this repository for more information.
#
# This script was created by Aryaman Rajaputra

import geopandas as gpd
from matplotlib.patches import Patch
import matplotlib.pyplot as plt
import numpy as np

def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)

    https://stackoverflow.com/questions/29545704/fast-haversine-approximation-python-pandas
    """
    # Convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat/2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2.0)**2
    c = 2 * np.arcsin(np.sqrt(a))
    r = 6371
    return c * r

def plot_shapefile(shapefile_path):
    """
    Plot the shapefile via matplotlib
    """
    gdf = gpd.read_file(shapefile_path)

    if gdf.crs is None:
        gdf.crs = "EPSG:4326"

    fig, ax = plt.subplots(figsize=(10, 8))

    buffer_distance_km = 10
    avg_latitude = gdf.geometry.centroid.y.mean()
    km_to_deg_lon = buffer_distance_km / (haversine(0, avg_latitude, 1, avg_latitude))
    km_to_deg_lat = buffer_distance_km / (haversine(0, avg_latitude, 0, avg_latitude + 1))

    buffers_deg = gdf.geometry.buffer(km_to_deg_lon)
    buffers_deg = buffers_deg.buffer(km_to_deg_lat)
    buffers_plot = buffers_deg.plot(ax=ax, facecolor='none', edgecolor='red', linewidth=2, label='Buffers (10 km)')

    gdf_plot = gdf.plot(ax=ax, color='blue', alpha=0.5, label='Telecom Features')

    legend_handles = [Patch(facecolor='none', edgecolor='red', label='Buffers (10 km)'),
                      plt.Rectangle((0, 0), 1, 1, fc='blue', alpha=0.5, label='Telecom Features')]

    ax.legend(handles=legend_handles)

    plt.title('Telecom Lines')
    plt.xlabel('Longitude (degrees)')
    plt.ylabel('Latitude (degrees)')
    plt.show()

if __name__ == "__main__":
    shapefile_path = input("Enter the path to the shapefile: ")
    plot_shapefile(shapefile_path)
