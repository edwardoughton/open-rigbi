#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# canada_processing.py file for OpenRigbi, created to help with processing the data files from Canada.
#
# SPDX-FileCopyrightText: 2024 Aryaman Rajaputra <arajaput@gmu.edu>
# SPDX-License-Identifier: MIT
#
# Note: The programs and configurations used by this script may not be under the same license.
# Please check the LICENSING file in the root directory of this repository for more information.
#
# This script was created by Aryaman Rajaputra

import numpy as np
import pandas as pd
import geopandas as gpd

from shapely import Point

import os
from pathlib import Path

BASE_PATH: str = './data'
DATA_FOLDER: Path = Path('./data')
DATA_RAW: str = os.path.join(BASE_PATH, 'raw')
DATA_INTERMEDIATE: str = os.path.join(BASE_PATH, 'intermediate')
DATA_PROCESSED: str = os.path.join(BASE_PATH, 'processed')
EXPORTS_FOLDER: Path = DATA_FOLDER / 'exports'
EXPORTS_FOLDER.mkdir(parents=True, exist_ok=True)

DIRECTORY_PATH = f"{DATA_PROCESSED}/CAN/regions"

def create_buffers(provinces, companies):
    for province in provinces:
        for company in companies:
            gdf = gpd.read_file(f"{DIRECTORY_PATH}/{province}_{company}.shp")
            gdf['geometry'] = gdf['geometry'].buffer(0.01)
            gdf.to_file(f"{DIRECTORY_PATH}/{province}_{company}_buffer.shp")

def k_means(k, points):
    centroids = []
    clusters = [[] for _ in range(k)]
    converged = False
    while not converged:
        clusters = [[] for _ in range(k)]
        for point in points:
            distances = [np.linalg.norm(np.array(point) - np.array(centroid)) for centroid in centroids]
            cluster_assign = clusters[distances.index(min(distances))].append(point)
            clusters[cluster_assign].append(point)

        new_centroids = [np.mean(cluster, axis=0) for cluster in clusters]
        converged = np.array_equal(centroids, new_centroids)
        centroids = new_centroids

    if converged:
        return clusters

if __name__ == "__main__":
    if not os.path.exists(DIRECTORY_PATH):
        os.makedirs(DIRECTORY_PATH)
    province_list = ['AB', 'BC', 'MB', 'NB', 'NL', 'NS', 'NT', 'NU', 'ON', 'PE', 'QC', 'SK', 'YT']
    can_radio = pd.read_csv(f"../data/raw/countries_data/CAN/Site_Data_Extract.csv", encoding="latin1", dtype=object)
    for province in province_list:
        province_data = can_radio[can_radio['PROV'] == province]
        province_data_rogers = province_data[province_data['LICENSEE'].str.contains('Rogers', case=False)]
        province_data_bell = province_data[province_data['LICENSEE'].str.contains('Bell', case=False)]
        province_data_telus = province_data[province_data['LICENSEE'].str.contains('Telus', case=False)]

        province_data_rogers['geometry'] = province_data_rogers.apply(lambda row: Point(float(row.LONGITUDE), float(row.LATITUDE)), axis=1)
        province_data_bell['geometry'] = province_data_bell.apply(lambda row: Point(float(row.LONGITUDE), float(row.LATITUDE)), axis=1)
        province_data_telus['geometry'] = province_data_telus.apply(lambda row: Point(float(row.LONGITUDE), float(row.LATITUDE)), axis=1)

        gdf_rogers = gpd.GeoDataFrame(province_data_rogers, geometry='geometry')
        gdf_bell = gpd.GeoDataFrame(province_data_bell, geometry='geometry')
        gdf_telus = gpd.GeoDataFrame(province_data_telus, geometry='geometry')

        gdf_rogers.to_file(f"{DIRECTORY_PATH}/{province}_rogers.shp")
        gdf_bell.to_file(f"{DIRECTORY_PATH}/{province}_bell.shp")
        gdf_telus.to_file(f"{DIRECTORY_PATH}/{province}_telus.shp")

    create_buffers(province_list, ['rogers', 'bell', 'telus'])
