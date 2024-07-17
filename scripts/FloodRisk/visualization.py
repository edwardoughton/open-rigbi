#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# visualization.py file for FloodRisk, designed to visalize risk to telecom
# infrastructure due to flooding. This file visualizes buffer zones and affected telecom stations.
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

MCC_TO_COUNTRY = {
    276: 'ALB',
    505: 'AUS',
    302: 'CAN',
    712: 'CRI',
    234: 'GBR',
    607: 'GMB',
    639: 'KEN',
    204: 'NLD',
    530: 'NZL',
    608: 'SEN'
}

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
    gdf = gpd.read_file(shapefile_path, crs=4326)

    # Create the subplot graph window for the display
    fig, ax = plt.subplots(figsize=(10, 8))

    # Set the buffer distance
    buffer_distance_km = 10

    # Get the centroid latitude and longitude, using the haversine formula to convert to km
    avg_latitude = gdf.geometry.centroid.y.mean()
    lon_deg_per_km = 1 / haversine(0, avg_latitude, 1, avg_latitude)
    lat_deg_per_km = 1 / haversine(0, avg_latitude, 0, avg_latitude + 1)

    # Get the lat lon calculation in the buffer
    buffers_deg = gdf.geometry.buffer(buffer_distance_km * lon_deg_per_km)
    buffers_deg = buffers_deg.buffer(buffer_distance_km * lat_deg_per_km)
    buffers_plot = buffers_deg.plot(ax=ax, facecolor='none', edgecolor='red', linewidth=2, label='Buffers (10 km)')

    # Plot this to the screen
    gdf_plot = gdf.plot(ax=ax, color='blue', alpha=0.5, label='Telecom Features')

    # Create the legend with the buffers
    legend_handles = [Patch(facecolor='none', edgecolor='red', label='Buffers (10 km)'),
                      plt.Rectangle((0, 0), 1, 1, fc='blue', alpha=0.5, label='Telecom Features')]
    ax.legend(handles=legend_handles, loc='upper right')

    # Create axes and plot labels
    plt.title('Telecom Infrastructure and Buffers')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')

    plt.show()

def plot_bar(lengths, radio_len):
    fig, ax = plt.subplots(figsize=(10, 6))
    countries = [x['Country'] for x in lengths]
    unique_stations = [x['Unique 4G Stations'] for x in lengths]
    unique_bs_id_int = [x['Unique BS ID Int'] for x in lengths]
    unique_sector_id_int = [x['Unique Sector ID Int'] for x in lengths]

    bar_width = 0.25
    r1 = np.arange(len(countries))
    r2 = [x + bar_width for x in r1]
    r3 = [x + bar_width for x in r2]
    r4 = [x + bar_width for x in r3]

    country_names = [MCC_TO_COUNTRY[mcc] for mcc in countries]

    # Adjusted plotting values
    plt.bar(r1, [y / 10 for y in unique_stations], color='blue', width=bar_width, label='Unique 4G Stations')
    plt.bar(r2, [y / 10 for y in unique_bs_id_int], color='green', width=bar_width, label='Unique BS ID Int')
    plt.bar(r3, [y / 10 for y in unique_sector_id_int], color='red', width=bar_width, label='Unique Sector ID Int')
    plt.bar(r4, radio_len, color='yellow', width=bar_width, label='Radio Data Length')

    plt.xlabel('Country')
    plt.ylabel('Count')
    plt.title('Comparison of Data Lengths by Country')
    plt.xticks([r + bar_width for r in range(len(country_names))], country_names, rotation=45)
    plt.legend()

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    shapefile_path = input("Enter the path to the shapefile: ")
    plot_shapefile(shapefile_path)
